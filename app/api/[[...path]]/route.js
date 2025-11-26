import { NextResponse } from 'next/server';

// API route handler for the portfolio website
// Currently serves as a placeholder for future functionality

export async function GET(request) {
  const { pathname } = new URL(request.url);

  // Health check endpoint
  if (pathname === '/api/health') {
    return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() });
  }

  // Default response for undefined routes
  return NextResponse.json(
    { message: 'Portfolio API', version: '1.0.0' },
    { status: 200 }
  );
}

export async function POST(request) {
  const { pathname } = new URL(request.url);

  // Example: Contact form endpoint (placeholder)
  if (pathname === '/api/contact') {
    try {
      const body = await request.json();
      // In production, you would handle email sending or database storage here
      return NextResponse.json(
        { message: 'Message received', success: true },
        { status: 200 }
      );
    } catch (error) {
      return NextResponse.json(
        { message: 'Invalid request', success: false },
        { status: 400 }
      );
    }
  }

  return NextResponse.json(
    { message: 'Not found' },
    { status: 404 }
  );
}
