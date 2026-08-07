import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../models/api_parsers.dart';
import '../../models/analysis_result.dart';
import '../../models/history_item.dart';
import '../history_repository.dart';

/// Backend-backed [HistoryRepository] reading from the Chai AI HTTP API.
///
/// History is created by the backend whenever an image is analyzed, so `save`
/// is a no-op and `clear` deletes the listed entries. Favorite toggling has no
/// backend endpoint yet, so it is persisted only for the current session.
class ApiHistoryRepository implements HistoryRepository {
  final String baseUrl;
  final http.Client _client;

  // Session-only favorite overrides (the backend has no favorite endpoint yet).
  final Set<String> _favorites = {};

  ApiHistoryRepository(this.baseUrl, {http.Client? client})
      : _client = client ?? http.Client();

  @override
  Future<List<HistoryItem>> fetchAll() async {
    final uri = Uri.parse('$baseUrl/v1/history').replace(queryParameters: {
      'page': '1',
      'limit': '100',
    });
    final response = await _client.get(uri);
    final body = _decodeObject(response);
    if (body == null) {
      throw http.ClientException('Backend returned ${response.statusCode}.');
    }
    final items = (body['items'] as List<dynamic>? ?? [])
        .map((e) => parseHistoryItem(e as Map<String, dynamic>))
        .toList();
    return items.map((item) {
      if (_favorites.contains(item.id)) return item.copyWith(isFavorite: true);
      return item;
    }).toList();
  }

  @override
  Future<AnalysisResult> fetchDetail(String id) async {
    final response = await _client.get(Uri.parse('$baseUrl/v1/history/$id'));
    final body = _decodeObject(response);
    if (body == null) {
      throw http.ClientException(
        'Backend returned ${response.statusCode} for history detail.',
      );
    }
    return parseAnalysisResult(body);
  }

  @override
  Future<void> save(HistoryItem item) async {
    // The backend persists history when an image is analysed; nothing to do.
  }

  @override
  Future<void> remove(String id) async {
    await _client.delete(Uri.parse('$baseUrl/v1/history/$id'));
    _favorites.remove(id);
  }

  @override
  Future<void> toggleFavorite(String id) async {
    if (_favorites.contains(id)) {
      _favorites.remove(id);
    } else {
      _favorites.add(id);
    }
  }

  @override
  Future<void> clear() async {
    final items = await fetchAll();
    for (final item in items) {
      await _client.delete(Uri.parse('$baseUrl/v1/history/${item.id}'));
    }
    _favorites.clear();
  }

  Map<String, dynamic>? _decodeObject(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw http.ClientException(
        _errorMessage(response) ?? 'Backend returned ${response.statusCode}.',
        response.request?.url,
      );
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  String? _errorMessage(http.Response response) {
    try {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      final error = (body as Map<String, dynamic>)['error'];
      if (error is Map<String, dynamic> && error['message'] is String) {
        return error['message'] as String;
      }
    } catch (_) {
      // Ignore; fall back to the generic message.
    }
    return null;
  }
}