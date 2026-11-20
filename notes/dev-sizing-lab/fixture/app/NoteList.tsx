'use client';

import { useState } from 'react';
import Link from 'next/link';
import { notes } from './notes';

export default function NoteList() {
  const [filter, setFilter] = useState('');
  const query = filter.trim().toLowerCase();
  return <><label>Filter notes <input value={filter} onChange={event => setFilter(event.target.value)} /></label>
    {notes.filter(note => note[1].toLowerCase().includes(query)).map(([slug,title,summary]) =>
      <article key={slug}><h2><Link href={`/notes/${slug}`}>{title}</Link></h2><p>{summary}</p></article>)}
  </>;
}
