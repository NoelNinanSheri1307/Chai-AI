import 'dart:typed_data';

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../core/utils/formatters.dart';
import '../models/analysis_result.dart';
import '../models/verdict.dart';

/// Renders the branded PDF report structured around Authenticity Detection
/// and Image Insights.
class PdfReportBuilder {
  static Future<Uint8List> build(AnalysisResult result) async {
    final doc = pw.Document();
    final prov = result.provenance;
    final isSightengineOk = prov?.isSightengineAvailable ?? false;

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        build: (_) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'Chai AI',
              style: pw.TextStyle(
                fontSize: 22,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.Text(
              'Digital Authenticity & Forensic Insights Report',
              style: const pw.TextStyle(fontSize: 11, color: PdfColors.grey700),
            ),
            pw.Divider(),
            pw.SizedBox(height: 6),
            _kv('Analyzed file', result.fileName ?? 'Image'),
            _kv('Timestamp', AppFormatters.dateTime(result.timestamp)),
            _kv('Analysis duration',
                AppFormatters.duration(result.analysisDuration)),
            pw.SizedBox(height: 12),

            // FEATURE 1: AUTHENTICITY DETECTION
            _section('1. Authenticity Detection'),
            pw.Container(
              padding: const pw.EdgeInsets.all(12),
              decoration: pw.BoxDecoration(
                color: PdfColor.fromHex(_verdictHex(result.verdict)),
                borderRadius: pw.BorderRadius.circular(6),
              ),
              child: pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text(
                    result.verdict.label.toUpperCase(),
                    style: pw.TextStyle(
                      fontSize: 16,
                      fontWeight: pw.FontWeight.bold,
                      color: PdfColors.white,
                    ),
                  ),
                  pw.Text(
                    '${(result.confidence * 100).round()}% confidence',
                    style: const pw.TextStyle(
                      fontSize: 12,
                      color: PdfColors.white,
                    ),
                  ),
                ],
              ),
            ),
            pw.SizedBox(height: 6),
            pw.Text(
              isSightengineOk
                  ? 'Classification Decision: Primary Sightengine (70%) + Chai Forensic Support (30%)'
                  : 'Classification Decision: Chai Forensic Analysis (External verification unavailable)',
              style: pw.TextStyle(fontSize: 9, color: PdfColors.grey700),
            ),
            pw.SizedBox(height: 6),
            pw.Paragraph(text: result.explanation),
            pw.SizedBox(height: 12),

            // FEATURE 2: IMAGE INSIGHTS
            _section('2. Image Insights (Chai Forensic Pipeline)'),
            pw.Text(
              'Supporting indicators extracted from image analysis; not standalone proof of generation.',
              style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600),
            ),
            pw.SizedBox(height: 6),
            ...result.scores.map(
              (s) => pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 3),
                child: pw.Row(
                  mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                  children: [
                    pw.Text(s.category.label,
                        style: const pw.TextStyle(fontSize: 10)),
                    pw.Text(
                      '${(s.value * 100).round()}%',
                      style: pw.TextStyle(
                        fontSize: 10,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            pw.SizedBox(height: 10),

            _section('Detected Indicators'),
            if (result.indicators.isEmpty)
              pw.Text('No indicators above the confidence threshold.',
                  style: const pw.TextStyle(fontSize: 9))
            else
              ...result.indicators.map(
                (i) => pw.Padding(
                  padding: const pw.EdgeInsets.only(bottom: 4),
                  child: pw.Row(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('• ', style: const pw.TextStyle(fontSize: 9)),
                      pw.Expanded(
                        child: pw.Text(
                          '${i.type.label} (${i.severity}, ${(i.confidence * 100).round()}%) - ${i.description}',
                          style: const pw.TextStyle(fontSize: 9),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            pw.SizedBox(height: 10),

            _section('Image Metadata'),
            ...result.metadata.entries.where((e) => !e.key.startsWith('prov:')).map(
              (e) => pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 2),
                child: pw.Row(
                  mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                  children: [
                    pw.Text(e.key, style: const pw.TextStyle(fontSize: 9)),
                    pw.Text(e.value,
                        style: pw.TextStyle(
                            fontSize: 9, fontWeight: pw.FontWeight.bold)),
                  ],
                ),
              ),
            ),

            if (prov != null) ...[
              pw.SizedBox(height: 10),
              _section('Decision Provenance'),
              _kv('Fused AI Probability',
                  '${(prov.finalFusedProbability * 100).toStringAsFixed(1)}%'),
              _kv('Sightengine Status', prov.sightengineStatus),
              _kv('Chai AI Probability',
                  '${(prov.chaiAiProbability * 100).toStringAsFixed(1)}%'),
            ],

            pw.Spacer(),
            pw.Divider(),
            pw.SizedBox(height: 4),
            pw.Text(
              'Generated by Chai AI - Forensic Analysis & Authenticity Report.',
              style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey500),
            ),

          ],
        ),
      ),
    );
    return doc.save();
  }

  static pw.Widget _kv(String key, String value) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 3),
        child: pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(key,
                style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey600)),
            pw.Text(value,
                style:
                    pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold)),
          ],
        ),
      );

  static pw.Widget _section(String title) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 4),
        child: pw.Text(
          title,
          style: pw.TextStyle(
            fontSize: 11,
            fontWeight: pw.FontWeight.bold,
            color: PdfColors.grey900,
          ),
        ),
      );

  static String _verdictHex(Verdict verdict) {
    switch (verdict) {
      case Verdict.original:
        return '0E9F6E';
      case Verdict.aiEdited:
        return 'D97706';
      case Verdict.aiGenerated:
        return 'DC2626';
    }
  }
}

