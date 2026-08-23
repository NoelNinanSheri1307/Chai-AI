/// Application configuration & environment provider for Chai AI frontend.
class AppConfig {
  /// Default local development backend URL.
  static const String defaultLocalApiUrl = 'http://127.0.0.1:8000';

  /// Compile-time environment override via `--dart-define=API_BASE_URL=https://...`
  static const String apiBaseUrlOverride = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Default API base URL for the active build.
  /// If [API_BASE_URL] was provided at build time (e.g. `flutter build web --dart-define=API_BASE_URL=https://<RENDER_SERVICE>.onrender.com`),
  /// it is used; otherwise it defaults to local development `http://127.0.0.1:8000`.
  static String get initialApiBaseUrl {
    if (apiBaseUrlOverride.trim().isNotEmpty) {
      return apiBaseUrlOverride.trim().replaceAll(RegExp(r'/+$'), '');
    }
    return defaultLocalApiUrl;
  }

  /// Clean normalization for any configured API base URL.
  static String normalizeUrl(String url) {
    var trimmed = url.trim();
    if (trimmed.isEmpty) return defaultLocalApiUrl;
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      trimmed = 'https://$trimmed';
    }
    return trimmed.replaceAll(RegExp(r'/+$'), '');
  }
}
