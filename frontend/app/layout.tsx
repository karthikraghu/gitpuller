import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "GitPuller — Learning Progress Tracker",
    description:
        "Track what you learn from your GitHub commits, powered by AI.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
