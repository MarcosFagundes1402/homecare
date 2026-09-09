import 'package:app/historico_relatorios.dart';
import 'package:app/minhas_administracoes.dart';
import 'package:flutter/material.dart';

class PacienteDetalhes extends StatelessWidget {
  final Map paciente;
  final String token;

  const PacienteDetalhes({
    super.key,
    required this.paciente,
    required this.token,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Detalhes do paciente')),

      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Nome: ${paciente['nome']}'),
          Text('CPF: ${paciente['cpf']}'),
          Text('Nascimento: ${paciente['data_nascimento']}'),
          Text('Contato: ${paciente['tel']}'),
          Text('Endereço: ${paciente['endereco']}'),
          Text('Status: ${paciente['status']}'),

          const SizedBox(height: 30),

          ElevatedButton(
            onPressed: () {
              // depois abre registrar administração
            },
            child: const Text('Registrar administração'),
          ),

          const SizedBox(height: 10),

          ElevatedButton(
            onPressed: () {
              // abrir medicamentos do paciente
            },
            child: const Text('Ver medicamentos'),
          ),

          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => HistoricoRelatorios(
                    pacienteId: paciente['id'],
                    token: token,
                  ),
                ),
              );
            },
            child: const Text('Ver histórico de relatórios'),
          ),
          const SizedBox(height: 10),
          ElevatedButton(
            onPressed: () {
              // ir para ver administracoes
            },
            child: const Text('Ver histórico de administrações'),
          ),

          const SizedBox(height: 10),

          ElevatedButton(
            onPressed: () {
              // ir para criar tela de cria relatorio
            },
            child: const Text('Criar relatório diário'),
          ),

          const SizedBox(height: 10),
        ],
      ),
    );
  }
}
