import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:the_ai_law_helper/model/message.dart';

import '../utils/app_theme.dart';

class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: 
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!message.isUser) _buildBotAvatar(),
          if (!message.isUser) const SizedBox(width: 12),
          
          Flexible(
            child: Column(
              crossAxisAlignment: message.isUser 
                  ? CrossAxisAlignment.end 
                  : CrossAxisAlignment.start,
              children: [
                _buildMessageBubble(context),
                if (!message.isUser && message.sources.isNotEmpty)
                  _buildSources(),
                if (!message.isUser && message.metadata != null)
                  _buildMetadata(),
              ],
            ),
          ),
          
          if (message.isUser) const SizedBox(width: 12),
          if (message.isUser) _buildUserAvatar(),
        ],
      ),
    );
  }

  Widget _buildUserAvatar() {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        gradient: AppTheme.primaryGradient,
        shape: BoxShape.circle,
      ),
      child: const Icon(
        Icons.person_rounded,
        color: Colors.white,
        size: 20,
      ),
    );
  }

  Widget _buildBotAvatar() {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: message.isError ? AppTheme.errorColor : AppTheme.accentColor,
        shape: BoxShape.circle,
      ),
      child: Icon(
        message.isError ? Icons.error_rounded : Icons.balance,
        color: Colors.white,
        size: 20,
      ),
    );
  }

  Widget _buildMessageBubble(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.75,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: message.isUser 
            ? AppTheme.primaryColor 
            : (message.isError ? AppTheme.errorColor.withOpacity(0.1) : AppTheme.surfaceColor),
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(16),
          topRight: const Radius.circular(16),
          bottomLeft: Radius.circular(message.isUser ? 16 : 4),
          bottomRight: Radius.circular(message.isUser ? 4 : 16),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (message.text.contains('*') || message.text.contains('#')) 
            MarkdownBody(
              data: message.text,
              styleSheet: MarkdownStyleSheet(
                p: AppTheme.bodyMedium.copyWith(
                  color: message.isUser ? Colors.white : AppTheme.textPrimary,
                ),
                strong: AppTheme.bodyMedium.copyWith(
                  fontWeight: FontWeight.bold,
                  color: message.isUser ? Colors.white : AppTheme.textPrimary,
                ),
              ),
            )
          else
            Text(
              message.text,
              style: message.text.contains('মৌলিক') || message.text.contains('সংবিধান')
                  ? AppTheme.bengaliText.copyWith(
                      color: message.isUser ? Colors.white : AppTheme.textPrimary,
                    )
                  : AppTheme.bodyMedium.copyWith(
                      color: message.isUser ? Colors.white : AppTheme.textPrimary,
                    ),
            ),
          
          const SizedBox(height: 8),
          
          Text(
            _formatTimestamp(message.timestamp),
            style: AppTheme.bodySmall.copyWith(
              color: message.isUser 
                  ? Colors.white.withOpacity(0.7) 
                  : AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSources() {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'সূত্র:',
            style: AppTheme.bodySmall.copyWith(
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryColor,
            ),
          ),
          const SizedBox(height: 4),
          ...message.sources.take(3).map((source) => Container(
            margin: const EdgeInsets.only(bottom: 4),
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.accentColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: AppTheme.accentColor.withOpacity(0.3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  source.title,
                  style: AppTheme.bodySmall.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
                if (source.content.isNotEmpty)
                  Text(
                    source.content.length > 100 
                        ? '${source.content.substring(0, 100)}...'
                        : source.content,
                    style: AppTheme.bodySmall.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildMetadata() {
    final metadata = message.metadata!;
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.info_outline_rounded,
            size: 14,
            color: AppTheme.textSecondary,
          ),
          const SizedBox(width: 4),
          Text(
            '${metadata['llm_type'] ?? 'AI'} • ${metadata['retrieval_strategy'] ?? 'hybrid'}',
            style: AppTheme.bodySmall.copyWith(
              color: AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'এখনই';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes} মিনিট আগে';
    } else if (difference.inDays < 1) {
      return '${difference.inHours} ঘণ্টা আগে';
    } else {
      return '${timestamp.day}/${timestamp.month}/${timestamp.year}';
    }
  }
}