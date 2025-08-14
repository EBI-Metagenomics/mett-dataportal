export function cacheResponse(duration: number, keyGenerator?: (...args: any[]) => string) {
    const cacheMap = new Map<string, { result: any; timestamp: number }>();

    return function (_target: any, _propertyKey: string, descriptor: PropertyDescriptor) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            // Generate cache key based on provided function or use first argument
            const cacheKey = keyGenerator ? keyGenerator(...args) : args[0];

            const cached = cacheMap.get(cacheKey);
            if (cached && (Date.now() - cached.timestamp < duration)) {
                return cached.result;
            }

            const result = await originalMethod.apply(this, args);
            cacheMap.set(cacheKey, {result, timestamp: Date.now()});
            return result;
        };

        return descriptor;
    };
}
