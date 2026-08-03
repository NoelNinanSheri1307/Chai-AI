class AppFormatters {
  static String percent(double value) =>
      '${(value.clamp(0.0, 1.0) * 100).round()}%';

  static String percentOneDecimal(double value) =>
      '${(value.clamp(0.0, 1.0) * 100).toStringAsFixed(1)}%';

  static String duration(Duration d) {
    if (d.inMilliseconds < 1000) return '${d.inMilliseconds}ms';
    return '${(d.inMilliseconds / 1000).toStringAsFixed(1)}s';
  }

  static String date(DateTime dt) {
    final local = dt.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(local.day)} ${_month(local.month)} ${local.year}';
  }

  static String dateTime(DateTime dt) {
    final local = dt.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${date(local)} · ${two(local.hour)}:${two(local.minute)}';
  }

  static String time(DateTime dt) {
    final local = dt.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(local.hour)}:${two(local.minute)}';
  }

  static String relative(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    if (diff.inDays < 30) return '${(diff.inDays / 7).round()}w ago';
    return date(dt);
  }

  static String _month(int m) {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return months[m - 1];
  }
}
