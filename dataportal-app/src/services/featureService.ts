import { ApiService } from './api';

export interface FeatureFlags {
  pyhmmer_search: boolean;
}

export class FeatureService {
  private static features: FeatureFlags | null = null;
  private static loading = false;

  /**
   * Get available features from the backend
   */
  static async getFeatures(): Promise<FeatureFlags> {
    if (this.features !== null) {
      return this.features;
    }

    if (this.loading) {
      // Wait for the ongoing request to complete
      while (this.loading) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      return this.features!;
    }

    try {
      this.loading = true;
      const response = await ApiService.get<FeatureFlags>('/features');
      this.features = response;
      return response;
    } catch (error) {
      console.error('Failed to fetch feature flags:', error);
      // Return default values if feature flags can't be fetched
      this.features = {
        pyhmmer_search: false
      };
      return this.features;
    } finally {
      this.loading = false;
    }
  }

  /**
   * Check if a specific feature is enabled
   */
  static async isFeatureEnabled(feature: keyof FeatureFlags): Promise<boolean> {
    const features = await this.getFeatures();
    return features[feature] || false;
  }

  /**
   * Clear cached features (useful for testing or when features change)
   */
  static clearCache(): void {
    this.features = null;
  }
} 