import {useSearchParams} from 'react-router-dom'
import {useCallback} from 'react'

export const useUrlState = () => {
    const [searchParams, setSearchParams] = useSearchParams()

    const updateUrl = useCallback((updates: Record<string, string | string[] | null>) => {
        const newParams = new URLSearchParams(searchParams)

        Object.entries(updates).forEach(([key, value]) => {
            if (value === null) {
                newParams.delete(key)
            } else if (Array.isArray(value)) {
                newParams.delete(key)
                if (value.length > 0) {
                    value.forEach(v => newParams.append(key, v))
                }
            } else {
                newParams.set(key, value)
            }
        })

        setSearchParams(newParams, {replace: true})
    }, [searchParams, setSearchParams])

    const getParam = useCallback((key: string): string | null => {
        return searchParams.get(key)
    }, [searchParams])

    const getParams = useCallback((key: string): string[] => {
        return searchParams.getAll(key)
    }, [searchParams])

    return {
        searchParams,
        updateUrl,
        getParam,
        getParams,
    }
}
