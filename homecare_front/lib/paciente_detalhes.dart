import 'package:app/criar_relatorio.dart';
import 'package:app/cuidador_administracoes.dart';
import 'package:app/historico_relatorios.dart';
import 'package:app/medicamentos_paciente.dart';
import 'package:flutter/material.dart';
import 'package:app/registrar_administracao.dart';

class PacienteDetalhes extends StatelessWidget {
  final Map paciente;
  final String token;
  final bool modoAdmin;

  const PacienteDetalhes({
    super.key,
    required this.paciente,
    required this.token,
    this.modoAdmin = false,
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
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => RegistrarAdministracao(
                    pacienteId: paciente['id'],
                    pacienteNome: paciente['nome'],
                    token: token,
                  ),
                ),
              );
            },
            child: const Text('Registrar administração'),
          ),

          const SizedBox(height: 10),

          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => MedicamentosPaciente(
                    pacienteNome: paciente['nome'],
                    pacienteId: paciente['id'],
                    token: token,
                  ),
                ),
              );
            },
            child: const Text('Ver medicamentos'),
          ),

          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => HistoricoRelatorios(
                    pacienteNome: paciente['nome'],
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
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => CuidadorAdministracoes(
                    pacienteNome: paciente['nome'],
                    pacienteId: paciente['id'],
                    token: token,
                    modoAdmin: modoAdmin,
                  ),
                ),
              );
            },
            child: const Text('Ver histórico de administrações'),
          ),

          const SizedBox(height: 10),

          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => CriarRelatorio(
                    pacienteId: paciente['id'],
                    pacienteNome: paciente['nome'],
                    token: token,
                  ),
                ),
              );
            },
            child: const Text('Criar relatório diário'),
          ),

          const SizedBox(height: 10),
        ],
      ),
    );
  }
}
