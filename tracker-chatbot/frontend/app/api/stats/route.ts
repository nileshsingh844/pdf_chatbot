import { NextResponse } from 'next/server';

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
    console.error('Stats proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
