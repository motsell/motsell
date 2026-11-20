"""Bounded local synthetic Next.js build/smoke observation; run only in the task VM."""
from pathlib import Path
import datetime, hashlib, json, os, re, shutil, signal, subprocess, sys, time, urllib.request, urllib.error

ROOT=Path(__file__).resolve().parent
assert ROOT.name=='motsell-next-sizing' and str(ROOT).startswith('/home/')
assert os.uname().sysname=='Linux' and os.uname().machine=='aarch64'
APP=ROOT/'fixture'; REPORT=ROOT/'evidence'; REPORT.mkdir(mode=0o700,exist_ok=True)
NODE=ROOT/'node-v24.22.3-linux-arm64/bin/node'; NPM=ROOT/'node-v24.22.3-linux-arm64/bin/npm'
NEXT=APP/'node_modules/next/dist/bin/next'
ENV={**os.environ,'PATH':str(NODE.parent)+':'+os.environ.get('PATH',''),'NEXT_TELEMETRY_DISABLED':'1','CI':'1','npm_config_update_notifier':'false','npm_config_audit':'false','npm_config_fund':'false'}
assert NODE.is_file() and NEXT.is_file()
os.umask(0o077)

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def mem():
    out={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name,value=line.split(':',1)
        if name in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):out[name]=int(value.split()[0])
    return out
def oom():
    return int(next(line.split()[1] for line in Path('/proc/vmstat').read_text().splitlines() if line.startswith('oom_kill ')))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest():
    files=[APP/name for name in ('package.json','package-lock.json','tsconfig.json')]
    files.extend(p for directory in ('app','public') for p in (APP/directory).rglob('*') if p.is_file())
    assert all(p.is_file() and not p.is_symlink() for p in files)
    return {str(p.relative_to(APP)):sha(p) for p in sorted(files)}
def command(args):return subprocess.check_output([str(x) for x in args],env=ENV,text=True,cwd=APP).strip()
def emit(name,obj):
    (REPORT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');print(json.dumps(obj,sort_keys=True),flush=True)
def clean_generated():
    build_dir=APP/'.next'
    assert not build_dir.is_symlink()
    if build_dir.exists():shutil.rmtree(build_dir)
    for name in ('tsconfig.tsbuildinfo',):
        p=APP/name
        if p.exists():assert p.is_file() and not p.is_symlink();p.unlink()
def build(label,phase,attempt):
    if phase=='clean-run':clean_generated()
    else:assert (APP/'.next').is_dir()
    log=REPORT/f'{label}-{phase}-{attempt}.log'; baseline=mem(); low=baseline['MemAvailable']; swap_low=baseline['SwapFree']; before=oom(); start=time.monotonic(); utc=now();timeout=False
    with log.open('wb') as stream:
        process=subprocess.Popen([str(NODE),str(NEXT),'build'],cwd=APP,env=ENV,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        while process.poll() is None:
            sample=mem();low=min(low,sample['MemAvailable']);swap_low=min(swap_low,sample['SwapFree'])
            if time.monotonic()-start>125:
                timeout=True;os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
                break
            time.sleep(.1)
        code=process.wait(); sample=mem(); low=min(low,sample['MemAvailable']);swap_low=min(swap_low,sample['SwapFree']);elapsed=time.monotonic()-start
    result={'profile':label,'phase':phase,'attempt':attempt,'started_at_utc':utc,'wall_seconds':round(elapsed,3),'exit_code':code,'timeout':timeout,'guest_mem_total_kib':baseline['MemTotal'],'guest_mem_available_before_kib':baseline['MemAvailable'],'guest_mem_available_min_sampled_kib':low,'guest_mem_available_after_kib':sample['MemAvailable'],'guest_swap_total_kib':baseline['SwapTotal'],'guest_swap_free_min_sampled_kib':swap_low,'guest_oom_kill_delta':oom()-before,'memory_sample_interval_seconds':.1,'build_dir_preexisting':phase!='clean-run','metric':'guest-wide MemAvailable sampled, not process or cgroup RSS; kernel file-cache/other guest processes included','source_manifest_unchanged':manifest()==FROZEN}
    emit(f'{label}-{phase}-{attempt}.json',result)
    return result
def request(path):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:r=opener.open('http://127.0.0.1:3030'+path,timeout=4)
    except urllib.error.HTTPError as e:r=e
    with r:return r.status,r.read(),r.headers.get('Cache-Control','')
def serve(label):
    log=REPORT/f'{label}-serve.log'; checks={}; baseline=mem(); low=baseline['MemAvailable'];start=time.monotonic()
    with log.open('wb') as stream:
        proc=subprocess.Popen([str(NODE),str(NEXT),'start','-H','127.0.0.1','-p','3030'],cwd=APP,env=ENV,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            for _ in range(80):
                if proc.poll() is not None:raise RuntimeError('server exited')
                try:
                    code,body,_=request('/')
                    if code==200 and b'motsell-next-fixture-home-v1' in body:break
                except OSError:pass
                time.sleep(.25)
            else:raise RuntimeError('server not ready')
            cases=[('/',200,b'motsell-next-fixture-home-v1'),('/notes/overview',200,b'motsell-next-fixture-note-v1-overview'),('/notes/conclusion',200,b'motsell-next-fixture-note-v1-conclusion'),('/fixture.svg',200,b'<svg'),('/notes/not-in-fixture',404,None)]
            for url,expected,marker in cases:
                status,body,_=request(url)
                # React can put HTML comments between a text prefix and a dynamic
                # slug. Join that markup boundary before asserting literal text.
                marker_present=marker is None or marker in re.sub(rb'<!--.*?-->',b'',body,flags=re.S)
                assert status==expected and marker_present, f'{url}: HTTP {status}, expected {expected}, marker_present={marker_present}'
                checks[url]=status;low=min(low,mem()['MemAvailable'])
            status,body,cache=request('/api/status');assert status==200 and json.loads(body)=={'marker':'motsell-next-fixture-api-v1','status':'ok'} and 'no-store' in cache
            checks['/api/status']=status;checks['/api/status_exact_json_no_store']=True
            return {'profile':label,'actual_localhost_only':True,'runtime_routes':checks,'startup_and_check_seconds':round(time.monotonic()-start,3),'guest_mem_available_before_kib':baseline['MemAvailable'],'guest_mem_available_min_observed_kib':min(low,mem()['MemAvailable']),'load_test':False}
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()

label=sys.argv[1]; assert label in ('2c4g','4c8g')
expected_cpu,expected_ram=(2,4) if label=='2c4g' else (4,8)
assert len(os.sched_getaffinity(0))==expected_cpu and (expected_ram-.5)*1024**2<mem()['MemTotal']<=expected_ram*1024**2
frozen_path=REPORT/'frozen-source-manifest.json'
if not frozen_path.exists():frozen_path.write_text(json.dumps(manifest(),indent=2,sort_keys=True)+'\n')
FROZEN=json.loads(frozen_path.read_text());assert manifest()==FROZEN and 'package-lock.json' in FROZEN
emit(f'{label}-environment'+('-smoke' if len(sys.argv)>2 else '')+'.json',{'profile':label,'started_at_utc':now(),'architecture':os.uname().machine,'os_release':Path('/etc/os-release').read_text(),'kernel':os.uname().release,'affinity_cpus':len(os.sched_getaffinity(0)),'memory_kib':mem(),'node_version':command([NODE,'--version']),'npm_version':command([NPM,'--version']),'next_version':command([NODE,NEXT,'--version']),'package_lock_sha256':FROZEN['package-lock.json'],'source_manifest_sha256':sha(frozen_path),'boot_id_sha256':sha(Path('/proc/sys/kernel/random/boot_id')),'disk_total_bytes':shutil.disk_usage(ROOT).total,'disk_free_bytes':shutil.disk_usage(ROOT).free})
if len(sys.argv)>2:
    assert sys.argv[2]=='smoke-only'
    emit(f'{label}-runtime.json',serve(label));assert manifest()==FROZEN
    expected_records=[json.loads((REPORT/f'{label}-{phase}-{attempt}.json').read_text()) for attempt in (1,2,3) for phase in ('clean-run','repeat-warm')]
    assert all(r['exit_code']==0 and r['source_manifest_unchanged'] for r in expected_records)
    emit(f'{label}-complete.json',{'profile':label,'builds':6,'clean_runs':3,'repeat_warm_runs':3,'all_exit_zero':True,'source_unchanged':True,'runtime_smoke_pass':True,'runtime_harness_rerun':True})
    sys.exit(0)
passed=[]
for attempt in (1,2,3):
    for phase in ('clean-run','repeat-warm'):
        result=build(label,phase,attempt);passed.append(result)
        if result['exit_code']!=0 or not result['source_manifest_unchanged']:
            emit(f'{label}-halt.json',{'reason':'build failed or source changed','result':result});sys.exit(1)
emit(f'{label}-runtime.json',serve(label))
assert manifest()==FROZEN
emit(f'{label}-complete.json',{'profile':label,'builds':len(passed),'clean_runs':3,'repeat_warm_runs':3,'all_exit_zero':True,'source_unchanged':True,'runtime_smoke_pass':True})
