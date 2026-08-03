import '../models/analysis_result.dart';
import '../models/history_item.dart';

/// Contract for persisted analysis history.
///
/// The mock implementation stores entries locally (and seeds a realistic
/// dataset). An [ApiHistoryRepository] backed by the future backend will
/// implement the same interface with near-zero UI impact.
abstract class HistoryRepository {
  Future<List<HistoryItem>> fetchAll();

  /// Full report for a stored history entry.
  Future<AnalysisResult> fetchDetail(String id);

  Future<void> save(HistoryItem item);

  Future<void> remove(String id);

  Future<void> toggleFavorite(String id);

  Future<void> clear();
}
