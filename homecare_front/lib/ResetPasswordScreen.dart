import 'package:flutter/material.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String email;

  const ResetPasswordScreen({super.key, required this.email});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreen();
}

class _ResetPasswordScreen extends State<ResetPasswordScreen> {
  final senhaController = TextEditingController();
  final confirmarSenhaController = TextEditingController();

  bool mostrarSenha = false;
  bool mostrarConfirmarSenha = false;

  void alterarSenha() {
    final senha = senhaController.text;
    final confirmarSenha = confirmarSenhaController.text;

    if (senha.isEmpty || confirmarSenha.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Preencha todos os campos')));
      return;
    }

    if (senha != confirmarSenha) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('As senha não coincidem')));
      return;
    }

    print('EMAIL: ${widget.email}');
    print('NOVA SENHA: $senha');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('voltar')),

      body: Center(
        child: SizedBox(
          width: 320,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Nova senha',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 20),

              TextField(
                controller: senhaController,
                obscureText: !mostrarSenha,
                decoration: InputDecoration(
                  labelText: 'Nova senha',
                  border: const OutlineInputBorder(),
                  suffixIcon: IconButton(
                    icon: Icon(
                      mostrarSenha ? Icons.visibility : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() {
                        mostrarSenha = !mostrarSenha;
                      });
                    },
                  ),
                ),
              ),

              const SizedBox(height: 20),

              TextField(
                controller: confirmarSenhaController,
                obscureText: !mostrarConfirmarSenha,
                decoration: InputDecoration(
                  labelText: 'Confirmar senha',
                  border: const OutlineInputBorder(),
                  suffixIcon: IconButton(
                    icon: Icon(
                      mostrarConfirmarSenha
                          ? Icons.visibility
                          : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() {
                        mostrarConfirmarSenha = !mostrarConfirmarSenha;
                      });
                    },
                  ),
                ),
              ),

              const SizedBox(height: 20),

              SizedBox(
                width: 150,
                height: 45,
                child: ElevatedButton(
                  onPressed: alterarSenha,
                  child: const Text('ALTERAR'),
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
    senhaController.dispose();
    confirmarSenhaController.dispose();
    super.dispose();
  }
}
