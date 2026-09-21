import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CriarUsuarios extends StatefulWidget {
  final String token;

  const CriarUsuarios({super.key, required this.token});

  @override
  State<CriarUsuarios> createState() => _CriarUsuariosState();
}

class _CriarUsuariosState extends State<CriarUsuarios> {
  final nomeController = TextEditingController();
  final emailController = TextEditingController();
  final senhaController = TextEditingController();
  final confirmarsenhaController = TextEditingController();

  final cpfController = TextEditingController();
  final nascimentoController = TextEditingController();
  final telController = TextEditingController();
  final enderecoController = TextEditingController();
  final obsController = TextEditingController();

  late final List<TextEditingController> controllers = [
    nomeController,
    emailController,
    senhaController,
    confirmarsenhaController,
    cpfController,
    nascimentoController,
    telController,
    enderecoController,
    obsController,
  ];

  String? roleSelecionada;

  Future<void> criarUsuarios() async {
    final url = Uri.parse('$baseUrl/usuarios/criar');

    final dados = {
      'nome': nomeController.text.trim(),
      'email': emailController.text.trim(),
      'senha': senhaController.text.trim(),
      'confirmar_senha': confirmarsenhaController.text.trim(),
      'role': roleSelecionada,
    };

    if (roleSelecionada == 'paciente' || roleSelecionada == 'cuidador') {
      dados.addAll({
        'cpf': cpfController.text.trim(),
        'data_nascimento': nascimentoController.text.trim(),
        'tel': telController.text.trim(),
        'endereco': enderecoController.text.trim(),
        'obs': obsController.text.trim(),
      });
    }

    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(dados),
      );

      final resposta = jsonDecode(response.body);

      if (!mounted) return;

      if (response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              resposta['msg']?.toString() ?? 'Usuário criado com sucesso.',
            ),
          ),
        );

        for (final controller in controllers) {
          controller.clear();
        }

        setState(() {
          roleSelecionada = null;
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(resposta['erro'] ?? 'Erro ao criar usuário.')),
        );
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Criar usuário'), actions: [LogoutButton()]),

      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Text(
                        'Criar usuário',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: nomeController,
                        decoration: const InputDecoration(
                          labelText: 'Nome',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: emailController,
                        decoration: const InputDecoration(
                          labelText: 'E-mail',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: senhaController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Senha',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: confirmarsenhaController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Confirmar senha',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(
                        initialValue: roleSelecionada,
                        decoration: const InputDecoration(
                          labelText: 'Função',
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(
                            value: 'admin',
                            child: Text('Administrador'),
                          ),

                          DropdownMenuItem(
                            value: 'cuidador',
                            child: Text('Cuidador'),
                          ),

                          DropdownMenuItem(
                            value: 'paciente',
                            child: Text('Paciente'),
                          ),
                        ],

                        onChanged: (valor) {
                          setState(() {
                            roleSelecionada = valor;
                          });
                        },
                      ),

                      if (roleSelecionada == 'paciente' ||
                          roleSelecionada == 'cuidador') ...[
                        const SizedBox(height: 20),

                        TextField(
                          controller: cpfController,
                          decoration: const InputDecoration(
                            labelText: 'CPF',
                            border: OutlineInputBorder(),
                          ),
                        ),

                        const SizedBox(height: 20),

                        TextField(
                          controller: nascimentoController,
                          decoration: const InputDecoration(
                            labelText: 'Data de nascimento',
                            border: OutlineInputBorder(),
                          ),
                        ),

                        const SizedBox(height: 20),

                        TextField(
                          controller: telController,
                          decoration: const InputDecoration(
                            labelText: 'Telefone',
                            border: OutlineInputBorder(),
                          ),
                        ),

                        const SizedBox(height: 20),

                        TextField(
                          controller: enderecoController,
                          decoration: const InputDecoration(
                            labelText: 'Endereço',
                            border: OutlineInputBorder(),
                          ),
                        ),
                        const SizedBox(height: 20),

                        TextField(
                          controller: obsController,
                          decoration: const InputDecoration(
                            labelText: 'Observações',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ],

                      const SizedBox(height: 20),

                      ElevatedButton(
                        onPressed: () {
                          criarUsuarios();
                        },
                        child: const Text('Criar'),
                      ),
                      // seus campos aqui
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    for (final controller in controllers) {
      controller.dispose();
    }

    super.dispose();
  }
}
