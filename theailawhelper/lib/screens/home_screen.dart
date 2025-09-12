import 'package:flutter/material.dart';
import 'package:animated_text_kit/animated_text_kit.dart';
import '../utils/app_theme.dart';
import '../widgets/feature_card.dart';
import '../widgets/quick_action_button.dart';
import 'chat_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppTheme.primaryColor,
              AppTheme.secondaryColor,
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Header Section
              _buildHeader(),
              
              // Content Section
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: const BoxDecoration(
                    color: AppTheme.backgroundColor,
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 20),
                        _buildWelcomeSection(),
                        const SizedBox(height: 30),
                        _buildQuickActions(context),
                        const SizedBox(height: 30),
                        _buildFeatures(),
                        const SizedBox(height: 30),
                        _buildRecentQuestions(),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.balance,
              color: AppTheme.goldColor,
              size: 32,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'বাংলা এআই ল হেল্পার',
                  style: AppTheme.bengaliText.copyWith(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Bangladesh AI Law Helper',
                  style: AppTheme.bodyMedium.copyWith(
                    color: Colors.white.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () {},
            icon: const Icon(
              Icons.notifications_rounded,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'স্বাগতম! 🙏',
          style: AppTheme.headingLarge.copyWith(
            color: AppTheme.primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 60,
          child: AnimatedTextKit(
            animatedTexts: [
              TypewriterAnimatedText(
                'বাংলাদেশের সংবিধান ও আইন সম্পর্কে জিজ্ঞাসা করুন',
                textStyle: AppTheme.bengaliText.copyWith(
                  fontSize: 16,
                  color: AppTheme.textSecondary,
                ),
                speed: const Duration(milliseconds: 100),
              ),
              TypewriterAnimatedText(
                'Ask questions about Bangladesh Constitution & Laws',
                textStyle: AppTheme.bodyLarge.copyWith(
                  color: AppTheme.textSecondary,
                ),
                speed: const Duration(milliseconds: 80),
              ),
            ],
            repeatForever: true,
            pause: const Duration(milliseconds: 2000),
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'দ্রুত শুরু করুন',
          style: AppTheme.headingMedium,
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: QuickActionButton(
                icon: Icons.chat_bubble_rounded,
                title: 'নতুন প্রশ্ন',
                subtitle: 'চ্যাট শুরু করুন',
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => const ChatScreen(),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: QuickActionButton(
                icon: Icons.gavel_rounded,
                title: 'সংবিধান',
                subtitle: 'মৌলিক অধিকার',
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => const ChatScreen(
                        initialQuery: 'বাংলাদেশের সংবিধানে মৌলিক অধিকার কী কী?',
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildFeatures() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'বৈশিষ্ট্যসমূহ',
          style: AppTheme.headingMedium,
        ),
        const SizedBox(height: 16),
        const FeatureCard(
          icon: Icons.translate_rounded,
          title: 'দ্বিভাষিক সহায়তা',
          subtitle: 'বাংলা ও ইংরেজি উভয় ভাষায় প্রশ্ন করুন',
          color: AppTheme.accentColor,
        ),
        const SizedBox(height: 12),
        const FeatureCard(
          icon: Icons.psychology_rounded,
          title: 'কৃত্রিম বুদ্ধিমত্তা',
          subtitle: 'উন্নত AI দিয়ে সঠিক উত্তর পান',
          color: AppTheme.goldColor,
        ),
        const SizedBox(height: 12),
        const FeatureCard(
          icon: Icons.security_rounded,
          title: 'নির্ভরযোগ্য তথ্য',
          subtitle: 'অফিসিয়াল আইনি দলিল থেকে তথ্য',
          color: AppTheme.primaryColor,
        ),
      ],
    );
  }

  Widget _buildRecentQuestions() {
    final recentQuestions = [
      'প্রধানমন্ত্রীর ক্ষমতা ও দায়িত্ব কী?',
      'What are fundamental rights?',
      'সংসদের গঠন কেমন?',
      'Marriage laws in Bangladesh',
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'সাম্প্রতিক প্রশ্নাবলী',
          style: AppTheme.headingMedium,
        ),
        const SizedBox(height: 16),
        ...recentQuestions.map((question) => Container(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: const Icon(
              Icons.help_outline_rounded,
              color: AppTheme.primaryColor,
            ),
            title: Text(
              question,
              style: AppTheme.bodyMedium,
            ),
            trailing: const Icon(
              Icons.arrow_forward_ios_rounded,
              size: 16,
              color: AppTheme.textSecondary,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            tileColor: AppTheme.surfaceColor,
            onTap: () {
              // Navigate to chat with this question
            },
          ),
        )),
      ],
    );
  }
}