export const dynamic = 'force-dynamic';

export function GET() {
  return Response.json({marker:'motsell-next-fixture-api-v1', status:'ok'}, {headers:{'Cache-Control':'no-store'}});
}
