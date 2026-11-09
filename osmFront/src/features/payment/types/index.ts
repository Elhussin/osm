// use in payment page
export interface PayPalButtonProps {
    clientId?: string;
    planId?: string;
    planDirection?: string;
    label?: string;
    method?: string;
    amount?: string;
    planName?: string;
  };
  

export type PricingPlansProps = {
    clientId?: string;
};

export interface PaymentProcessingModalProps {
    isOpen: boolean;
    message?: string;
}
  