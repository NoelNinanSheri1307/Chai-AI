import 'dart:typed_data';

import 'package:printing/printing.dart';
import 'package:share_plus/share_plus.dart';

/// Thin wrapper around printing/share_plus so screens never talk to plugins
/// directly.
class ShareService {
  Future<void> shareText(String text) async {
    await Share.share(text);
  }

  Future<void> sharePdf(Uint8List bytes, String filename) async {
    await Printing.sharePdf(bytes: bytes, filename: filename);
  }

  Future<void> printPdf(Uint8List bytes) async {
    await Printing.layoutPdf(onLayout: (_) async => bytes);
  }
}
