/// Application configuration & environment provider for Chai AI frontend.
class AppConfig {
  /// Permanent Render backend API URL.
  static const String defaultApiUrl = 'https://chaiaibackend.onrender.com';

  /// Compile-time environment override via `--dart-define=API_BASE_URL=https://...`
  static const String apiBaseUrlOverride = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Default API base URL for the active build.
  /// Always routes to https://chaiaibackend.onrender.com unless explicitly overridden.
  static String get initialApiBaseUrl {
    if (apiBaseUrlOverride.trim().isNotEmpty) {
      return apiBaseUrlOverride.trim().replaceAll(RegExp(r'/+$'), '');
    }
    return defaultApiUrl;
  }

  /// Clean normalization for any configured API base URL.
  static String normalizeUrl(String url) {
    var trimmed = url.trim();
    if (trimmed.isEmpty) return defaultApiUrl;
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      trimmed = 'https://$trimmed';
    }
    return trimmed.replaceAll(RegExp(r'/+$'), '');
  }
}

