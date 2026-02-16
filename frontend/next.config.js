/** @type {import('next').NextConfig} */
const nextConfig = {
    // Proxy API requests to the Python FastAPI backend during development.
    // This avoids CORS issues — your React code calls /api/* and Next.js
    // forwards those requests to the FastAPI server running on port 8000.
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: "http://localhost:8000/api/:path*",
            },
        ];
    },
};

module.exports = nextConfig;
