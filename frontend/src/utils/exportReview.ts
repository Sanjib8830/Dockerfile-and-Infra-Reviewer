/**
 * Safe review export actions: copy diff, copy corrected content, and download.
 * These utilities never mutate the caller's submitted/original content.
 */

export async function copyToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}

export function downloadTextFile(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
