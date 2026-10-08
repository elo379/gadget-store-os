import { NextRequest } from "next/server";

const BACKEND =
  process.env.NEXT_BACKEND_API_URL || "http://127.0.0.1:8000";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const target = `${BACKEND}/${path.join("/")}${request.nextUrl.search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.text();
  }

  try {
    const response = await fetch(target, init);
    const body = await response.arrayBuffer();

    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("transfer-encoding");

    return new Response(body, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "Backend service unavailable." },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
