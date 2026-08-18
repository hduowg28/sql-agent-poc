// frontend/src/types/vulnerable.ts
// Type definitions for Vulnerable Lab API responses

export interface SQLInjectionResponse {
  success: boolean;
  mode: string;
  raw_sql_executed: string;
  secure_sql_equivalent: string;
  result: string;
  sandbox_note: string;
  injection_detected: boolean;
  injection_payload: string | null;
}

export interface SubscribeResponse {
  success: boolean;
  mode: string;
  llm_prompt_used: string;
  llm_raw_response: string;
  action_taken: string;
  injection_detected: boolean;
  injection_analysis: string;
  secure_approach: string;
}

export interface VulnerabilityInfo {
  id: string;
  type: string;
  category: string;
  endpoint: string;
  description: string;
  demo_payload: string;
}

export interface VulnerableLabInfo {
  lab_name: string;
  purpose: string;
  vulnerabilities_demonstrated: VulnerabilityInfo[];
  safety_note: string;
}

export interface CommandInjectionResponse {
  success: boolean;
  mode: string;
  attack_chain: string;
  llm_prompt_used: string;
  llm_raw_response: string;
  tool_called: string;
  to_address_passed_to_tool: string;
  vulnerable_shell_command: string;
  injection_detected: boolean;
  inner_command_extracted: string | null;
  command_executed: string | null;
  command_output: string | null;
  dns_exfiltration_simulated: string | null;
  exploit_technique: string;
  secure_fix: string;
}
