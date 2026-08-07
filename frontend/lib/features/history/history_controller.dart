import 'package:flutter/foundation.dart';

import '../../models/history_item.dart';
import '../../models/verdict.dart';
import '../../repositories/history_repository.dart';

enum HistorySort {
  newest('Newest'),
  oldest('Oldest'),
  confidenceHigh('Confidence ↑'),
  confidenceLow('Confidence ↓');

  final String label;
  const HistorySort(this.label);
}

/// Owns history state and delegates persistence to a [HistoryRepository].
/// Swapping the repository implementation has zero impact on the UI.
class HistoryController extends ChangeNotifier {
  final HistoryRepository _repository;

  List<HistoryItem> _items = [];
  bool _loading = true;
  String _query = '';
  Verdict? _verdictFilter;
  bool _favoritesOnly = false;
  HistorySort _sort = HistorySort.newest;

  HistoryController(this._repository);

  bool get loading => _loading;
  String get query => _query;
  Verdict? get verdictFilter => _verdictFilter;
  bool get favoritesOnly => _favoritesOnly;
  HistorySort get sort => _sort;

  List<HistoryItem> get items {
    var list = List<HistoryItem>.of(_items);
    if (_favoritesOnly) {
      list = list.where((e) => e.isFavorite).toList();
    }
    if (_verdictFilter != null) {
      list = list.where((e) => e.verdict == _verdictFilter).toList();
    }
    final q = _query.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list
          .where((e) => (e.fileName ?? '').toLowerCase().contains(q))
          .toList();
    }
    switch (_sort) {
      case HistorySort.newest:
        list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
      case HistorySort.oldest:
        list.sort((a, b) => a.timestamp.compareTo(b.timestamp));
      case HistorySort.confidenceHigh:
        list.sort((a, b) => b.confidence.compareTo(a.confidence));
      case HistorySort.confidenceLow:
        list.sort((a, b) => a.confidence.compareTo(b.confidence));
    }
    return list;
  }

  Future<void> load() async {
    _loading = true;
    notifyListeners();
    try {
      _items = await _repository.fetchAll();
    } catch (_) {
      // A failed history fetch (e.g. backend offline) must never crash the UI;
      // degrade gracefully to an empty list.
      _items = [];
    }
    _loading = false;
    notifyListeners();
  }

  void setQuery(String value) {
    _query = value;
    notifyListeners();
  }

  void setSort(HistorySort value) {
    _sort = value;
    notifyListeners();
  }

  void setVerdictFilter(Verdict? value) {
    _verdictFilter = value;
    notifyListeners();
  }

  void setFavoritesOnly(bool value) {
    _favoritesOnly = value;
    notifyListeners();
  }

  Future<void> add(HistoryItem item) async {
    await _repository.save(item);
    await load();
  }

  Future<void> remove(String id) async {
    await _repository.remove(id);
    await load();
  }

  Future<void> toggleFavorite(String id) async {
    await _repository.toggleFavorite(id);
    await load();
  }

  Future<void> clear() async {
    await _repository.clear();
    await load();
  }
}
