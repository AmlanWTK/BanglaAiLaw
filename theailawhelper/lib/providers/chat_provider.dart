import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import 'package:the_ai_law_helper/model/message.dart';


class ChatProvider extends ChangeNotifier {
  static const String baseUrl = 'http://localhost:8000'; // Your backend URL
  
  List<Message> _messages = [];
  bool _isLoading = false;
  
  List<Message> get messages => _messages;
  bool get isLoading => _isLoading;

  Future<void> sendMessage(String text) async {
    // Add user message
    final userMessage = Message(
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );
    
    _messages.add(userMessage);
    _isLoading = true;
    notifyListeners();

    try {
      // Call your backend API
      final response = await _callLegalAPI(text);
      
      // Add bot response
      final botMessage = Message(
        text: response['answer'] ?? 'দুঃখিত, কোনো উত্তর পাওয়া যায়নি।',
        isUser: false,
        timestamp: DateTime.now(),
        sources: _extractSources(response),
        metadata: response['metadata'],
      );
      
      _messages.add(botMessage);
    } catch (e) {
      // Add error message
      final errorMessage = Message(
        text: 'দুঃখিত, একটি ত্রুটি ঘটেছে। পুনরায় চেষ্টা করুন।\nError: ${e.toString()}',
        isUser: false,
        timestamp: DateTime.now(),
        isError: true,
      );
      
      _messages.add(errorMessage);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>> _callLegalAPI(String query) async {
    final url = Uri.parse('$baseUrl/query');
    
    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'question': query,
        'retrieval_strategy': 'hybrid',
        'use_conversation': false,
      }),
    ).timeout(const Duration(seconds: 60)); // Increase timeout for Ollama

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('API call failed: ${response.statusCode}');
    }
  }

  List<MessageSource> _extractSources(Map<String, dynamic> response) {
    final sources = <MessageSource>[];
    
    if (response['source_documents'] != null) {
      for (final doc in response['source_documents']) {
        sources.add(MessageSource(
          title: _extractTitleFromSource(doc['source'] ?? ''),
          content: doc['content'] ?? '',
          source: doc['source'] ?? '',
          category: doc['category'] ?? '',
        ));
      }
    }
    
    return sources;
  }

  String _extractTitleFromSource(String source) {
    // Extract filename from path and make it readable
    final filename = source.split('\\').last.split('/').last;
    return filename
        .replaceAll('.txt', '')
        .replaceAll('.pdf', '')
        .replaceAll('_', ' ')
        .split(' ')
        .map((word) => word.isNotEmpty 
            ? word[0].toUpperCase() + word.substring(1).toLowerCase() 
            : '')
        .join(' ');
  }

  void clearMessages() {
    _messages.clear();
    notifyListeners();
  }

  // Get conversation history
  Future<void> loadConversationHistory() async {
    try {
      final url = Uri.parse('$baseUrl/conversation/history');
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        // Process conversation history if needed
      }
    } catch (e) {
      print('Error loading conversation history: $e');
    }
  }

  // Check API health
  Future<bool> checkAPIHealth() async {
    try {
      final url = Uri.parse('$baseUrl/health');
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // Get API stats
  Future<Map<String, dynamic>?> getAPIStats() async {
    try {
      final url = Uri.parse('$baseUrl/stats');
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('Error getting API stats: $e');
    }
    
    return null;
  }
}