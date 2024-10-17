export function extractIsolateName(suggestion: any): string {
  if (typeof suggestion === 'string') {
    const parts = suggestion.split(' - ');
    if (parts.length > 1) {
      return parts[1].split(' (')[0].trim();
    } else {
      return suggestion.split(' (')[0].trim();
    }
  } else if (suggestion && suggestion.isolate_name) {
    return suggestion.isolate_name.trim(); // Extract isolate_name from the object
  } else {
    return ''; // Return an empty string if suggestion is invalid
  }
}
