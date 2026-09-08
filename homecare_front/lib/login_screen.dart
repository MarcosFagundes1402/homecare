import 'dart:convert';

import 'package:app/forgot_password_screen.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:app/home_screen.dart';

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
    final email = emailController.text;
    final senha = senhaController.text;

    final url = Uri.parse('http://localhost:5000/login');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'senha': senha}),
      );

      if (!mounted) return;

      final dados = jsonDecode(response.body);

      if (response.statusCode == 200) {
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
      } else {
        if (!mounted) return;

        senhaController.clear();

        setState(() {
          mostrarSenha = false;
        });

        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(
            SnackBar(content: Text(dados['erro'] ?? 'Erro ao fazer login')),
          );
        return;
      }
    } catch (erro) {
      print('ERRO: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SizedBox(
          width: 320,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'LOGIN',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 30),

              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: 'E-mail',
                  border: OutlineInputBorder(),
                ),
              ),

              const SizedBox(height: 15),

              TextField(
                controller: senhaController,
                focusNode: senhaFocus,
                obscureText: !mostrarSenha,

                decoration: InputDecoration(
                  labelText: 'Senha',
                  border: OutlineInputBorder(),

                  suffixIcon: IconButton(
                    icon: Icon(
                      mostrarSenha ? Icons.visibility : Icons.visibility_off,
                    ),

                    onPressed: () {
                      setState(() {
                        mostrarSenha = !mostrarSenha;
                      });

                      senhaFocus.requestFocus();
                    },
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
                        builder: (context) => const 
                        ForgotPasswordScreen(),
                      ),
                    );
                  },
                  child: const Text('Esqueceu sua senha?'),
                ),
              ),

              const SizedBox(height: 20),

              SizedBox(
                width: 150,
                height: 45,
                child: ElevatedButton(
                  onPressed: fazerLogin,

                  style: ElevatedButton.styleFrom(
                    side: const BorderSide(color: Color.fromARGB(255, 0, 53, 97), width: 2),
                  ),

                  child: const Text('ENTRAR'),
                ),
              ),
            ],
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
