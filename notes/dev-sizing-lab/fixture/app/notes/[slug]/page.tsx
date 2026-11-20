import { notFound } from 'next/navigation';
import Link from 'next/link';
import { notes } from '../../notes';

export const dynamicParams = false;
export function generateStaticParams() { return notes.map(([slug])=>({slug})); }

export default async function Note({params}: {params: Promise<{slug:string}>}) {
  const {slug} = await params;
  const note=notes.find(candidate=>candidate[0]===slug);
  if(!note) notFound();
  return <article><h1>{note[1]}</h1><p>{note[2]}</p><p>motsell-next-fixture-note-v1-{slug}</p><Link href="/">All notes</Link></article>;
}
