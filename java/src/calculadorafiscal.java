import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.Map;

/**
 * Classe responsável por centralizar a lógica complexa de cálculos fiscais
 * e tributários (impostos, taxas, descontos) para negociações B2B na plataforma ZIPBUM.
 * * Esta classe é crucial para o módulo de importação e para o cálculo de impostos
 * estaduais (UF) que devem ser considerados nos preços finais.
 */
public class calculadorafiscal { // Nome da classe interna ajustado para o nome do arquivo

    // Simulação das Alíquotas de Imposto por Estado (UF)
    // Em um sistema real, isso viria de um banco de dados ou serviço externo,
    // mas aqui mockamos como 18% para SP e 12% para outros estados do Sul/Sudeste
    private static final Map<String, BigDecimal> ALIQUOTAS_ICMS = new HashMap<>();

    static {
        // Alíquotas de ICMS (Simulação)
        ALIQUOTAS_ICMS.put("SP", new BigDecimal("0.18"));
        ALIQUOTAS_ICMS.put("RJ", new BigDecimal("0.18"));
        ALIQUOTAS_ICMS.put("MG", new BigDecimal("0.18"));
        ALIQUOTAS_ICMS.put("SC", new BigDecimal("0.12"));
        ALIQUOTAS_ICMS.put("RS", new BigDecimal("0.12"));
        ALIQUOTAS_ICMS.put("BA", new BigDecimal("0.17"));
        ALIQUOTAS_ICMS.put("DF", new BigDecimal("0.18"));
    }

    /**
     * Retorna a alíquota de ICMS para um determinado estado (UF).
     *
     * @param uf Código do estado (ex: "SP", "RJ").
     * @return BigDecimal Alíquota do imposto (ex: 0.18 para 18%), ou 0.17 (padrão) se não encontrado.
     */
    public BigDecimal obterAliquotaICMS(String uf) {
        if (uf == null) {
            return BigDecimal.ZERO;
        }
        String ufUpper = uf.toUpperCase();
        return ALIQUOTAS_ICMS.getOrDefault(ufUpper, new BigDecimal("0.17")); // Padrão 17%
    }

    /**
     * Calcula o valor final de um produto após aplicar o imposto de ICMS do estado de destino.
     *
     * @param valorUnitario Valor unitário do produto sem imposto.
     * @param quantidade Quantidade de itens.
     * @param ufDestino UF do estado de destino para aplicação do imposto.
     * @return BigDecimal Valor total da negociação com ICMS aplicado.
     */
    public BigDecimal calcularValorTotalComImposto(
            BigDecimal valorUnitario, 
            int quantidade, 
            String ufDestino) {
        
        if (valorUnitario == null || valorUnitario.compareTo(BigDecimal.ZERO) <= 0 || quantidade <= 0) {
            return BigDecimal.ZERO;
        }

        BigDecimal aliquota = obterAliquotaICMS(ufDestino);
        
        // 1. Calcula o subtotal (valor unitário * quantidade)
        BigDecimal subtotal = valorUnitario.multiply(new BigDecimal(quantidade));
        
        // 2. Calcula o valor do imposto (subtotal * alíquota)
        BigDecimal valorImposto = subtotal.multiply(aliquota);
        
        // 3. Calcula o valor total (subtotal + valorImposto)
        BigDecimal valorTotal = subtotal.add(valorImposto);
        
        // 4. Arredonda o resultado para duas casas decimais
        return valorTotal.setScale(2, RoundingMode.HALF_UP);
    }
    
    /**
     * Calcula a diferença entre dois valores e retorna a porcentagem de desconto.
     *
     * @param precoBase Preço original (maior).
     * @param precoAtual Preço negociado (menor).
     * @return BigDecimal Porcentagem de desconto aplicada.
     */
    public BigDecimal calcularPorcentagemDesconto(BigDecimal precoBase, BigDecimal precoAtual) {
        if (precoBase == null || precoBase.compareTo(BigDecimal.ZERO) <= 0) {
            return BigDecimal.ZERO;
        }
        
        // Desconto = (Base - Atual) / Base * 100
        BigDecimal diferenca = precoBase.subtract(precoAtual);
        BigDecimal porcentagem = diferenca.divide(precoBase, 4, RoundingMode.HALF_UP)
                                          .multiply(new BigDecimal("100"));
                                          
        return porcentagem.setScale(2, RoundingMode.HALF_UP);
    }

    // --- Métodos de Aplicação de Regras de Negociação (Simulação) ---

    /**
     * Aplica o desconto de preço por volume e retorna o valor unitário final.
     * * @param valorUnitarioBase Valor unitário antes dos descontos.
     * @param fatorDesconto Fator de desconto (ex: 0.10 para 10%).
     * @return BigDecimal Novo valor unitário.
     */
    public BigDecimal aplicarDescontoPorVolume(BigDecimal valorUnitarioBase, BigDecimal fatorDesconto) {
        if (valorUnitarioBase == null) {
            return BigDecimal.ZERO;
        }
        // Novo Preço = Base * (1 - Fator)
        BigDecimal novoValor = valorUnitarioBase.multiply(
            BigDecimal.ONE.subtract(fatorDesconto)
        );
        return novoValor.setScale(2, RoundingMode.HALF_UP);
    }
}