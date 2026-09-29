import { unzip } from '@gmod/bgzf-filehandle';
import pako from 'pako';

/**
 * Decompress bgzip / gzip payloads for GFF files.
 * bgzip is many gzip members; pako.inflate alone stops after the first block.
 */
export async function decompressGffBytes(data: Uint8Array): Promise<Uint8Array> {
  try {
    return await unzip(data);
  } catch {
    // try next method
  }

  try {
    return new Uint8Array(pako.inflate(data));
  } catch {
    // try next method
  }

  try {
    return new Uint8Array(pako.inflateRaw(data));
  } catch {
    // try next method
  }

  if (typeof window !== 'undefined' && 'DecompressionStream' in window) {
    try {
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(data);
          controller.close();
        },
      });

      const decompressedStream = stream.pipeThrough(
        new DecompressionStream('gzip')
      );
      const reader = decompressedStream.getReader();
      const chunks: Uint8Array[] = [];

      let reading = true;
      while (reading) {
        const { done, value } = await reader.read();
        if (done) {
          reading = false;
        } else {
          chunks.push(value);
        }
      }

      const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
      const result = new Uint8Array(totalLength);
      let offset = 0;
      for (const chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
      }
      return result;
    } catch {
      // try next method
    }
  }

  try {
    return await unzip(data);
  } catch {
    console.warn('All decompression methods failed for bgzip file');
  }

  throw new Error('All decompression methods failed for bgzip file');
}

export function isGzipMagic(bytes: Uint8Array): boolean {
  return bytes[0] === 0x1f && bytes[1] === 0x8b;
}
