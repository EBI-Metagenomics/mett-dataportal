export function extractIsolateName(suggestion: string): string {
  const parts = suggestion.split(' - ');
  if (parts.length > 1) {
    return parts[1].split(' (')[0].trim();
  } else {
    return suggestion.split(' (')[0].trim();
  }
}
