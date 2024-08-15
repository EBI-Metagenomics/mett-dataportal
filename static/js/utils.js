export function extractIsolateName(suggestion) {
    // console.log("extract called....")
    const parts = suggestion.split(' - ');
    if (parts.length > 1) {
        console.log("isolate...." + parts[1].split(' (')[0].trim())
        return parts[1].split(' (')[0].trim(); // Extract and trim isolate name
    } else {
        console.log("scientific name...." + suggestion.split(' (')[0].trim())
        return suggestion.split(' (')[0].trim(); // Extract and trim scientific name
    }
}
