import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND_URL = 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/stats`);
    
    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Stats Error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    // During build, backend won't be running, so return a mock response
    if (process.env.NODE_ENV === 'production' && process.env.NEXT_PHASE === 'phase-production-build') {
      return NextResponse.json({
        documents: 0,
        chunks: 0,
        sessions: 0,
        total_tokens: 0,
        model: 'building...',
        vector_db: 'building...'
      });
    }
    
    console.error('Stats proxy error:', error);
    return NextResponse.json(
      { error: 'Backend unavailable' },
      { status: 503 }
    );
  }
}
