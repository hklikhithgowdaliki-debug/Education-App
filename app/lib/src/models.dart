class Paper {
  final String id;
  final String board;
  final String course;
  final String stream;
  final String group;
  final String semester;
  final String subject;
  final String code;
  final String year;
  final String type;
  final String url;
  final String source;

  const Paper({
    required this.id,
    required this.board,
    required this.course,
    required this.stream,
    required this.group,
    required this.semester,
    required this.subject,
    required this.code,
    required this.year,
    required this.type,
    required this.url,
    required this.source,
  });

  factory Paper.fromJson(Map<String, dynamic> j) => Paper(
        id: (j['id'] ?? j['url']).toString(),
        board: (j['board'] ?? '').toString(),
        course: (j['course'] ?? '').toString(),
        stream: (j['stream'] ?? '').toString(),
        group: (j['group'] ?? '').toString(),
        semester: (j['semester'] ?? '').toString(),
        subject: (j['subject'] ?? '').toString(),
        code: (j['code'] ?? '').toString(),
        year: (j['year'] ?? '').toString(),
        type: (j['type'] ?? '').toString(),
        url: (j['url'] ?? '').toString(),
        source: (j['source'] ?? '').toString(),
      );

  String get title => subject;

  String get subtitle => [
        if (year.isNotEmpty && !group.contains(year)) year,
        if (group.isNotEmpty) group,
        if (semester.isNotEmpty) semester,
        type,
      ].where((s) => s.isNotEmpty).join(' • ');

  String get fileName => '${url.hashCode.toUnsigned(32).toRadixString(16)}_${url.length}.pdf';

  bool matches(String q) {
    final hay = '$subject $code $board $course $stream $group $semester $year'.toLowerCase();
    return q.toLowerCase().split(RegExp(r'\s+')).where((t) => t.isNotEmpty).every(hay.contains);
  }
}

/// Browsing levels, from broadest to narrowest.
const browseLevels = ['board', 'stream', 'group', 'semester'];

String levelValue(Paper p, String level) {
  switch (level) {
    case 'board':
      return p.board;
    case 'stream':
      return p.stream;
    case 'group':
      return p.group;
    case 'semester':
      return p.semester;
  }
  return '';
}
