import 'dart:convert';

import 'package:app/admin/criar_usuarios.dart';
import 'package:app/auth/forgot_password_screen.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:app/admin/home_screen.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../config/api.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController();
  final senhaController = TextEditingController();

  final senhaFocus = FocusNode();

  bool mostrarSenha = false;

  Future<void> fazerLogin() async {
    FocusScope.of(context).unfocus();

    final email = emailController.text.trim().toLowerCase();
    final senha = senhaController.text;

    final url = Uri.parse('$baseUrl/login');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'senha': senha}),
      );

      debugPrint('STATUS LOGIN: ${response.statusCode}');
      debugPrint('BODY LOGIN: ${response.body}');

      if (!mounted) return;

      // LOGIN FALHOU
      if (response.statusCode != 200) {
        String mensagem = 'E-mail ou senha inválidos';

        try {
          final erro = jsonDecode(response.body);

          if (erro is Map && erro['erro'] != null) {
            mensagem = erro['erro'].toString();
          }
        } catch (_) {
          // mantém mensagem padrão
        }

        senhaController.clear();

        setState(() {
          mostrarSenha = false;
        });

        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(mensagem)));

        return; // MUITO IMPORTANTE
      }

      // SÓ CHEGA AQUI COM STATUS 200
      final dados = jsonDecode(response.body);

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => HomeScreen(
            nome: dados['usuario']['nome'],
            role: dados['usuario']['role'],
            token: dados['token'],
          ),
        ),
      );
    } catch (erro) {
      debugPrint('ERRO LOGIN: $erro');

      if (!mounted) return;

      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text('Erro ao conectar: $erro')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Image.asset(
                    'assets/images/logo.png',
                    width: 150,
                    height: 150,
                    fit: BoxFit.contain,
                  ),

                  const Text(
                    'Home Care',
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1565A8),
                    ),
                  ),

                  const SizedBox(height: 8),

                  const Text(
                    'Mais cuidado para quem sempre cuidou.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16, color: Color(0xFF64748B)),
                  ),

                  const SizedBox(height: 4),

                  const Text(
                    'Uma rede de apoio para idosos e cuidadores.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 14, color: Color(0xFF94A3B8)),
                  ),

                  const SizedBox(height: 30),

                  TextField(
                    controller: emailController,
                    keyboardType: TextInputType.emailAddress,
                    decoration: InputDecoration(
                      hintText: 'Seu E-mail',
                      prefixIcon: const Icon(
                        Icons.email_outlined,
                        color: Color(0xFF64748B),
                      ),
                      filled: true,
                      fillColor: const Color(0xFFF8FAFC),
                      contentPadding: const EdgeInsets.symmetric(
                        vertical: 18,
                        horizontal: 16,
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(color: Color(0xFFDCE5EC)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(
                          color: Color(0xFF35AEB6),
                          width: 2,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 15),

                  TextField(
                    controller: senhaController,
                    focusNode: senhaFocus,
                    obscureText: !mostrarSenha,

                    onSubmitted: (_) {
                      fazerLogin();
                    },

                    decoration: InputDecoration(
                      hintText: 'Sua senha',
                      prefixIcon: const Icon(
                        Icons.lock_outline,
                        color: Color(0xFF64748B),
                      ),
                      suffixIcon: IconButton(
                        icon: Icon(
                          mostrarSenha
                              ? Icons.visibility
                              : Icons.visibility_off,
                          color: Color(0xFF64748B),
                        ),
                        onPressed: () {
                          setState(() {
                            mostrarSenha = !mostrarSenha;
                          });

                          senhaFocus.requestFocus();
                        },
                      ),
                      filled: true,
                      fillColor: const Color(0xFFF8FAFC),
                      contentPadding: const EdgeInsets.symmetric(
                        vertical: 18,
                        horizontal: 16,
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(color: Color(0xFFDCE5EC)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: const BorderSide(
                          color: Color(0xFF35AEB6),
                          width: 2,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 8),

                  Align(
                    alignment: Alignment.center,
                    child: TextButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ForgotPasswordScreen(),
                          ),
                        );
                      },
                      child: const Text('Esqueceu sua senha?'),
                    ),
                  ),

                  const SizedBox(height: 8),

                  Align(
                    alignment: Alignment.center,
                    child: TextButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                CriarUsuarios(modoCadastro: true),
                          ),
                        );
                      },
                      child: const Text('Cadastrar'),
                    ),
                  ),

                  const SizedBox(height: 20),

                  SizedBox(
                    width: double.infinity,
                    height: 70,
                    child: InkWell(
                      onTap: fazerLogin,
                      borderRadius: BorderRadius.circular(20),
                      child: SvgPicture.asset(
                        'assets/icons/button_entrar.svg',
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    emailController.dispose();
    senhaController.dispose();
    senhaFocus.dispose();

    super.dispose();
  }
}
