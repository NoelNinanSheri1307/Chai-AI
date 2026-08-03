import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../models/analysis_result.dart';
import '../../models/history_item.dart';
import '../history_repository.dart';
import 'mock_data.dart';

class MockHistoryRepository implements HistoryRepository {
  static const String _storageKey = 'chai_history_v1';

  List<HistoryItem>? _cache;
  bool _loaded = false;

  Future<List<HistoryItem>> _ensureLoaded() async {
    if (_loaded) return _cache!;
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null && raw.isNotEmpty) {
      final decoded = jsonDecode(raw) as List<dynamic>;
      _cache = decoded
          .map((e) => HistoryItem.fromJson(e as Map<String, dynamic>))
          .toList();
    } else {
      _cache = MockData.seedHistory(60);
      await _persist();
    }
    _loaded = true;
    return _cache!;
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(_cache!.map((e) => e.toJson()).toList()),
    );
  }

  @override
  Future<List<HistoryItem>> fetchAll() async {
    final list = await _ensureLoaded();
    return List.of(list)..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }

  @override
  Future<AnalysisResult> fetchDetail(String id) async {
    final list = await _ensureLoaded();
    final item = list.firstWhere(
      (e) => e.id == id,
      orElse: () => throw StateError('History entry not found: $id'),
    );
    return MockData.fromHistoryItem(item);
  }

  @override
  Future<void> save(HistoryItem item) async {
    final list = await _ensureLoaded();
    list.removeWhere((e) => e.id == item.id);
    list.insert(0, item);
    await _persist();
  }

  @override
  Future<void> remove(String id) async {
    final list = await _ensureLoaded();
    list.removeWhere((e) => e.id == id);
    await _persist();
  }

  @override
  Future<void> toggleFavorite(String id) async {
    final list = await _ensureLoaded();
    final index = list.indexWhere((e) => e.id == id);
    if (index == -1) return;
    list[index] = list[index].copyWith(isFavorite: !list[index].isFavorite);
    await _persist();
  }

  @override
  Future<void> clear() async {
    final list = await _ensureLoaded();
    list.clear();
    await _persist();
  }
}
