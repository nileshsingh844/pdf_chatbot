import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND_URL = 'http://127.0.0.1:8000';

export async function DELETE(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get('session_id');
    
    const backendUrl = sessionId 
      ? `${BACKEND_URL}/api/reset?session_id=${sessionId}`
      : `${BACKEND_URL}/api/reset`;
    
    const response = await fetch(backendUrl, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Reset Error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Reset proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
