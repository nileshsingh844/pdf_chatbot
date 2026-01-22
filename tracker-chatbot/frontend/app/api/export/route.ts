import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND_URL = 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const sessionId = formData.get('session_id') as string;
    
    const response = await fetch(`${BACKEND_URL}/api/export`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Export Error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const blob = await response.blob();
    return new Response(blob, {
      headers: {
        'Content-Type': 'text/markdown',
        'Content-Disposition': `attachment; filename=conversation_${sessionId}.md`,
      },
    });
  } catch (error) {
    console.error('Export proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
