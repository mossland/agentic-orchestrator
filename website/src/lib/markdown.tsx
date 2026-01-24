'use client';

import { marked } from 'marked';
import { useMemo } from 'react';

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,  // Convert \n to <br>
  gfm: true,     // GitHub Flavored Markdown
});

/**
 * Render markdown content to HTML string
 */
export function renderMarkdown(content: string): string {
  if (!content) return '';

  try {
    // Parse markdown to HTML
    const html = marked.parse(content, { async: false }) as string;
    return html;
  } catch {
    return content;
  }
}

/**
 * Component to render markdown content
 */
export function MarkdownContent({
  content,
  className = ''
}: {
  content: string;
  className?: string;
}) {
  const html = useMemo(() => renderMarkdown(content), [content]);

  return (
    <div
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
