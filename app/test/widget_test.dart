import 'dart:convert';
import 'dart:io';

import 'package:edu_papers/src/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final catalog = jsonDecode(File('assets/catalog.json').readAsStringSync()) as Map<String, dynamic>;
  final papers = (catalog['papers'] as List).map((e) => Paper.fromJson(e as Map<String, dynamic>)).toList();

  test('catalog is non-empty and every paper has an https PDF url', () {
    expect(papers, isNotEmpty);
    for (final p in papers) {
      expect(p.url, startsWith('https://'));
      expect(p.board, isNotEmpty);
      expect(p.subject, isNotEmpty);
    }
  });

  test('paper ids are unique', () {
    expect(papers.map((p) => p.id).toSet().length, papers.length);
  });

  test('search matches across fields', () {
    final p = papers.first;
    expect(p.matches(p.subject.split(' ').first), isTrue);
    expect(p.matches('zzzz-not-a-subject'), isFalse);
  });
}
