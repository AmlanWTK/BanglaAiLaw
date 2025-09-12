import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../utils/app_theme.dart';
import '../providers/chat_provider.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('সম্পর্কে'),
        automaticallyImplyLeading: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildAppInfo(),
            const SizedBox(height: 30),
            _buildAPIStatus(),
            const SizedBox(height: 30),
            _buildFeatures(),
            const SizedBox(height: 30),
            _buildContact(),
          ],
        ),
      ),
    );
  }

  Widget _buildAppInfo() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.cardDecoration,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.balance,
              color: Colors.white,
              size: 40,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'বাংলা এআই ল হেল্পার',
            style: AppTheme.headingMedium.copyWith(
              color: AppTheme.primaryColor,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Bangladesh AI Law Helper',
            style: TextStyle(
              fontSize: 16,
              color: AppTheme.textSecondary,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'বাংলাদেশের সংবিধান ও আইন সম্পর্কে কৃত্রিম বুদ্ধিমত্তা চালিত সহায়ক। '
            'এই অ্যাপটি আপনাকে আইনি প্রশ্নের দ্রুত ও নির্ভরযোগ্য উত্তর প্রদান করে।',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppTheme.textPrimary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAPIStatus() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.api_rounded,
                color: AppTheme.primaryColor,
              ),
              const SizedBox(width: 12),
              Text(
                'API স্ট্যাটাস',
                style: AppTheme.headingSmall,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Consumer<ChatProvider>(
            builder: (context, chatProvider, child) {
              return FutureBuilder<bool>(
                future: chatProvider.checkAPIHealth(),
                builder: (context, snapshot) {
                  final isHealthy = snapshot.data ?? false;
                  return Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: isHealthy ? Colors.green : Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        isHealthy ? 'সংযুক্ত' : 'সংযুক্ত নয়',
                        style: AppTheme.bodyMedium.copyWith(
                          color: isHealthy ? Colors.green : Colors.red,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  );
                },
              );
            },
          ),
          const SizedBox(height: 8),
          Text(
            'Backend: http://localhost:8000',
            style: AppTheme.bodySmall.copyWith(
              color: AppTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatures() {
    final features = [
      {
        'icon': Icons.translate_rounded,
        'title': 'দ্বিভাষিক সহায়তা',
        'description': 'বাংলা ও ইংরেজি উভয় ভাষায় প্রশ্ন করুন',
      },
      {
        'icon': Icons.psychology_rounded,
        'title': 'কৃত্রিম বুদ্ধিমত্তা',
        'description': 'উন্নত AI মডেল ব্যবহার করে সঠিক উত্তর',
      },
      {
        'icon': Icons.security_rounded,
        'title': 'নির্ভরযোগ্য তথ্য',
        'description': 'অফিসিয়াল আইনি দলিল থেকে তথ্য সংগ্রহ',
      },
      {
        'icon': Icons.speed_rounded,
        'title': 'দ্রুত উত্তর',
        'description': 'তাৎক্ষণিক এবং নিখুঁত তথ্য প্রদান',
      },
    ];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'বৈশিষ্ট্যসমূহ',
            style: AppTheme.headingSmall,
          ),
          const SizedBox(height: 16),
          ...features.map((feature) => Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    feature['icon'] as IconData,
                    color: AppTheme.primaryColor,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        feature['title'] as String,
                        style: AppTheme.bodyMedium.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        feature['description'] as String,
                        style: AppTheme.bodySmall.copyWith(
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildContact() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'যোগাযোগ',
            style: AppTheme.headingSmall,
          ),
          const SizedBox(height: 16),
          const Text(
            'এই অ্যাপটি বাংলাদেশের আইনি সমুদায়ের জন্য তৈরি করা হয়েছে। '
            'কোনো সমস্যা বা পরামর্শ থাকলে আমাদের সাথে যোগাযোগ করুন।',
            style: TextStyle(
              color: AppTheme.textPrimary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'সংস্করণ: 1.0.0',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}