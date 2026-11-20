export const notes = [
  ['overview','Overview','This fictional project records a release and a short validation check.'],
  ['routing','Routing','The application renders a small static set of pages and links between them.'],
  ['assets','Assets','All assets are generated locally and loaded without an external service.'],
  ['configuration','Configuration','The example has no credentials or private runtime settings.'],
  ['build','Build','A local build creates static routes, client bundles and a runtime route.'],
  ['validation','Validation','A fixed response marker makes a smoke test straightforward.'],
  ['storage','Storage','This small example uses immutable in-memory content, not a database.'],
  ['navigation','Navigation','A simple searchable list is provided through a client component.'],
  ['observability','Observability','The benchmark records elapsed time and guest memory samples.'],
  ['operations','Operations','A running fixture is not a guarantee about production performance.'],
  ['recovery','Recovery','Real applications need separately tested recovery procedures.'],
  ['conclusion','Conclusion','Results describe only this exact synthetic workload.']
] as const;
