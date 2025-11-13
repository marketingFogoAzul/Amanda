// java-modules/src/main/java/com/zipbum/CalculadoraFiscal.java
package com.zipbum;

import java.util.HashMap;
import java.util.Map;

/**
 * Módulo para cálculos fiscais complexos (ex: ICMS, ST).
 * Esta é uma classe de exemplo e deve ser expandida com as regras de negócio reais.
 */
public class CalculadoraFiscal {

    // (Exemplo) Tabela de alíquotas de ICMS interestadual
    private static final Map<String, Double> ALIQUOTAS_ICMS = new HashMap<>();

    static {
        // Preenche as alíquotas (exemplo simplificado)
        ALIQUOTAS_ICMS.put("SP_BA", 0.07); // SP -> BA
        ALIQUOTAS_ICMS.put("SP_AM", 0.07);
        ALIQUOTAS_ICMS.put("SP_RJ", 0.12);
        ALIQUOTAS_ICMS.put("SP_MG", 0.12);
        ALIQUOTAS_ICMS.put("SP_ES", 0.12);
        ALIQUOTAS_ICMS.put("BA_SP", 0.12);
        ALIQUOTAS_ICMS.put("SP_SP", 0.18); // Alíquota interna de SP (exemplo)
    }

    /**
     * Calcula o valor do ICMS com base na origem e destino.
     * @param ufOrigem UF do Vendedor (ex: "SP")
     * @param ufDestino UF do Comprador (ex: "BA")
     * @param valorBase Valor da mercadoria
     * @return O valor do imposto ICMS
     */
    public double calcularICMS(String ufOrigem, String ufDestino, double valorBase) {
        String chave = ufOrigem.toUpperCase() + "_" + ufDestino.toUpperCase();
        double aliquota = ALIQUOTAS_ICMS.getOrDefault(chave, 0.12); // Padrão de 12% se não achar

        double valorICMS = valorBase * aliquota;
        
        // Arredonda para 2 casas decimais
        return Math.round(valorICMS * 100.0) / 100.0;
    }

    /**
     * Função principal (main) para ser chamada pelo ProcessadorPrincipal.
     */
    public static void main(String[] args) {
        // [0]=ufOrigem, [1]=ufDestino, [2]=valorBase
        if (args.length < 3) {
            System.err.println("Erro: Argumentos insuficientes para cálculo fiscal. (Esperado: UF_Origem UF_Destino Valor)");
            System.exit(1);
        }
        
        try {
            String ufOrigem = args[0];
            String ufDestino = args[1];
            double valorBase = Double.parseDouble(args[2]);
            
            CalculadoraFiscal calculadora = new CalculadoraFiscal();
            double icms = calculadora.calcularICMS(ufOrigem, ufDestino, valorBase);
            
            // Retorna o resultado para o Python (stdout)
            System.out.println(icms); 
            System.exit(0);

        } catch (NumberFormatException e) {
            System.err.println("Erro: Valor base inválido.");
            System.exit(1);
        }
    }
}