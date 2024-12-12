export function cacheResponse(duration: number) {
    let cache: { result: any; timestamp: number } | null = null;

    return function (_target: any, _propertyKey: string, descriptor: PropertyDescriptor) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            if (cache && (Date.now() - cache.timestamp < duration)) {
                return cache.result;
            }

            const result = await originalMethod.apply(this, args);
            cache = { result, timestamp: Date.now() };
            return result;
        };

        return descriptor;
    };
}
