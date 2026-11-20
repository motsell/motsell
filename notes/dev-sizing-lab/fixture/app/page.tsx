import Image from 'next/image';
import NoteList from './NoteList';

export default function Home() {
  return <><h1>Next sizing fixture</h1><p>motsell-next-fixture-home-v1</p>
    <Image src="/fixture.svg" alt="Three simple blue bars" width={260} height={120} unoptimized />
    <NoteList /></>;
}
