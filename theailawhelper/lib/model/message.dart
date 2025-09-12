class Message {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<MessageSource> sources;
  final Map<String, dynamic>? metadata;
  final bool isError;

  Message({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.sources = const [],
    this.metadata,
    this.isError = false,
  });

  Map<String, dynamic> toJson() {
    return {
      'text': text,
      'isUser': isUser,
      'timestamp': timestamp.toIso8601String(),
      'sources': sources.map((s) => s.toJson()).toList(),
      'metadata': metadata,
      'isError': isError,
    };
  }

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      text: json['text'],
      isUser: json['isUser'],
      timestamp: DateTime.parse(json['timestamp']),
      sources: (json['sources'] as List?)
          ?.map((s) => MessageSource.fromJson(s))
          .toList() ?? [],
      metadata: json['metadata'],
      isError: json['isError'] ?? false,
    );
  }
}

class MessageSource {
  final String title;
  final String content;
  final String source;
  final String category;

  MessageSource({
    required this.title,
    required this.content,
    required this.source,
    required this.category,
  });

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'content': content,
      'source': source,
      'category': category,
    };
  }

  factory MessageSource.fromJson(Map<String, dynamic> json) {
    return MessageSource(
      title: json['title'],
      content: json['content'],
      source: json['source'],
      category: json['category'],
    );
  }
}