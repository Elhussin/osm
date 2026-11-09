import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const AccountCurrencyEnum = z.enum(["USD", "EUR", "SAR"]);
const Account = z
  .object({
    id: z.number().int(),
    name: z.string().max(255),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    currency: AccountCurrencyEnum.optional(),
    user: z.number().int(),
  })
  .passthrough();
const PaginatedAccountList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Account),
  })
  .passthrough();
const AccountRequest = z
  .object({
    name: z.string().min(1).max(255),
    currency: AccountCurrencyEnum.optional(),
    user: z.number().int(),
  })
  .passthrough();
const PatchedAccountRequest = z
  .object({
    name: z.string().min(1).max(255),
    currency: AccountCurrencyEnum,
    user: z.number().int(),
  })
  .partial()
  .passthrough();
const TransactionTypeEnum = z.enum(["income", "expense"]);
const AccountingCategory = z
  .object({
    id: z.number().int(),
    name: z.string().max(100),
    category_type: TransactionTypeEnum,
    description: z.string().nullish(),
    parent: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedAccountingCategoryList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(AccountingCategory),
  })
  .passthrough();
const AccountingCategoryRequest = z
  .object({
    name: z.string().min(1).max(100),
    category_type: TransactionTypeEnum,
    description: z.string().nullish(),
    parent: z.number().int().nullish(),
  })
  .passthrough();
const PatchedAccountingCategoryRequest = z
  .object({
    name: z.string().min(1).max(100),
    category_type: TransactionTypeEnum,
    description: z.string().nullable(),
    parent: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const FinancialPeriod = z
  .object({
    id: z.number().int(),
    name: z.string().max(50),
    start_date: z.string(),
    end_date: z.string(),
    is_closed: z.boolean().optional(),
  })
  .passthrough();
const PaginatedFinancialPeriodList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(FinancialPeriod),
  })
  .passthrough();
const FinancialPeriodRequest = z
  .object({
    name: z.string().min(1).max(50),
    start_date: z.string(),
    end_date: z.string(),
    is_closed: z.boolean().optional(),
  })
  .passthrough();
const PatchedFinancialPeriodRequest = z
  .object({
    name: z.string().min(1).max(50),
    start_date: z.string(),
    end_date: z.string(),
    is_closed: z.boolean(),
  })
  .partial()
  .passthrough();
const JournalEntry = z
  .object({
    id: z.number().int(),
    debit_currency: z.string(),
    debit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    credit_currency: z.string(),
    credit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction: z.number().int(),
    account: z.number().int(),
  })
  .passthrough();
const PaginatedJournalEntryList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(JournalEntry),
  })
  .passthrough();
const JournalEntryRequest = z
  .object({
    debit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    credit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction: z.number().int(),
    account: z.number().int(),
  })
  .passthrough();
const PatchedJournalEntryRequest = z
  .object({
    debit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    credit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction: z.number().int(),
    account: z.number().int(),
  })
  .partial()
  .passthrough();
const IntervalEnum = z.enum(["monthly", "yearly"]);
const RecurringTransaction = z
  .object({
    id: z.number().int(),
    amount_currency: z.string(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_types: TransactionTypeEnum,
    interval: IntervalEnum,
    next_execution: z.string(),
    account: z.number().int(),
  })
  .passthrough();
const PaginatedRecurringTransactionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(RecurringTransaction),
  })
  .passthrough();
const RecurringTransactionRequest = z
  .object({
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_types: TransactionTypeEnum,
    interval: IntervalEnum,
    next_execution: z.string(),
    account: z.number().int(),
  })
  .passthrough();
const PatchedRecurringTransactionRequest = z
  .object({
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_types: TransactionTypeEnum,
    interval: IntervalEnum,
    next_execution: z.string(),
    account: z.number().int(),
  })
  .partial()
  .passthrough();
const Tax = z
  .object({
    id: z.number().int(),
    name: z.string().max(100),
    rate: z.string().regex(/^-?\d{0,3}(?:\.\d{0,2})?$/),
    effective_date: z.string(),
    is_active: z.boolean().optional(),
    description: z.string().nullish(),
  })
  .passthrough();
const PaginatedTaxList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Tax),
  })
  .passthrough();
const TaxRequest = z
  .object({
    name: z.string().min(1).max(100),
    rate: z.string().regex(/^-?\d{0,3}(?:\.\d{0,2})?$/),
    effective_date: z.string(),
    is_active: z.boolean().optional(),
    description: z.string().nullish(),
  })
  .passthrough();
const PatchedTaxRequest = z
  .object({
    name: z.string().min(1).max(100),
    rate: z.string().regex(/^-?\d{0,3}(?:\.\d{0,2})?$/),
    effective_date: z.string(),
    is_active: z.boolean(),
    description: z.string().nullable(),
  })
  .partial()
  .passthrough();
const Transaction = z
  .object({
    id: z.number().int(),
    date: z.string(),
    amount_currency: z.string(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_type: TransactionTypeEnum,
    description: z.string().nullish(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    account: z.number().int(),
    period: z.number().int(),
    category: z.number().int().nullish(),
    tax_rate: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedTransactionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Transaction),
  })
  .passthrough();
const TransactionRequest = z
  .object({
    date: z.string(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_type: TransactionTypeEnum,
    description: z.string().nullish(),
    account: z.number().int(),
    period: z.number().int(),
    category: z.number().int().nullish(),
    tax_rate: z.number().int().nullish(),
  })
  .passthrough();
const PatchedTransactionRequest = z
  .object({
    date: z.string(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    transaction_type: TransactionTypeEnum,
    description: z.string().nullable(),
    account: z.number().int(),
    period: z.number().int(),
    category: z.number().int().nullable(),
    tax_rate: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const BranchUsers = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    status: z.boolean().optional(),
    notes: z.string().nullish(),
    branch_id: z.number().int(),
    employee_id: z.number().int(),
  })
  .passthrough();
const PaginatedBranchUsersList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(BranchUsers),
  })
  .passthrough();
const BranchUsersRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    status: z.boolean().optional(),
    notes: z.string().nullish(),
    branch_id: z.number().int(),
    employee_id: z.number().int(),
  })
  .passthrough();
const PatchedBranchUsersRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    status: z.boolean(),
    notes: z.string().nullable(),
    branch_id: z.number().int(),
    employee_id: z.number().int(),
  })
  .partial()
  .passthrough();
const BranchTypeEnum = z.enum(["store", "branch"]);
const Branch = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
    branch_code: z.string(),
    branch_type: BranchTypeEnum,
    country: z.string().optional(),
    city: z.string().max(100).optional(),
    address: z.string().optional(),
    phone: z.string().max(20).optional(),
    email: z.string().max(254).email().optional(),
    is_main_branch: z.boolean().optional(),
    allows_online_orders: z.boolean().optional(),
    operating_hours: z.unknown().optional(),
  })
  .passthrough();
const PaginatedBranchList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Branch),
  })
  .passthrough();
const BranchRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
    branch_type: BranchTypeEnum,
    country: z.string().optional(),
    city: z.string().max(100).optional(),
    address: z.string().optional(),
    phone: z.string().max(20).optional(),
    email: z.string().max(254).email().optional(),
    is_main_branch: z.boolean().optional(),
    allows_online_orders: z.boolean().optional(),
    operating_hours: z.unknown().optional(),
  })
  .passthrough();
const PatchedBranchRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
    branch_type: BranchTypeEnum,
    country: z.string(),
    city: z.string().max(100),
    address: z.string(),
    phone: z.string().max(20),
    email: z.string().max(254).email(),
    is_main_branch: z.boolean(),
    allows_online_orders: z.boolean(),
    operating_hours: z.unknown(),
  })
  .partial()
  .passthrough();
const Campaign = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(255),
    description: z.string(),
    start_date: z.string(),
    end_date: z.string(),
    customers: z.array(z.number().int()).optional(),
  })
  .passthrough();
const PaginatedCampaignList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Campaign),
  })
  .passthrough();
const CampaignRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(255),
    description: z.string().min(1),
    start_date: z.string(),
    end_date: z.string(),
    customers: z.array(z.number().int()).optional(),
  })
  .passthrough();
const PatchedCampaignRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(255),
    description: z.string().min(1),
    start_date: z.string(),
    end_date: z.string(),
    customers: z.array(z.number().int()),
  })
  .partial()
  .passthrough();
const ComplaintStatusEnum = z.enum(["open", "resolved"]);
const Complaint = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    description: z.string(),
    status: ComplaintStatusEnum.optional(),
    customer: z.number().int(),
  })
  .passthrough();
const PaginatedComplaintList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Complaint),
  })
  .passthrough();
const ComplaintRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    description: z.string().min(1),
    status: ComplaintStatusEnum.optional(),
    customer: z.number().int(),
  })
  .passthrough();
const PatchedComplaintRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    description: z.string().min(1),
    status: ComplaintStatusEnum,
    customer: z.number().int(),
  })
  .partial()
  .passthrough();
const Contact = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    email: z.string().max(254).email(),
    phone: z.string().max(20),
    name: z.string().max(100),
    message: z.string().max(500),
  })
  .passthrough();
const PaginatedContactList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Contact),
  })
  .passthrough();
const ContactRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    email: z.string().min(1).max(254).email(),
    phone: z.string().min(1).max(20),
    name: z.string().min(1).max(100),
    message: z.string().min(1).max(500),
  })
  .passthrough();
const PatchedContactRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    email: z.string().min(1).max(254).email(),
    phone: z.string().min(1).max(20),
    name: z.string().min(1).max(100),
    message: z.string().min(1).max(500),
  })
  .partial()
  .passthrough();
const CustomerGroup = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
    description: z.string().optional(),
    customers: z.array(z.number().int()),
  })
  .passthrough();
const PaginatedCustomerGroupList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(CustomerGroup),
  })
  .passthrough();
const CustomerGroupRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
    description: z.string().optional(),
    customers: z.array(z.number().int()),
  })
  .passthrough();
const PatchedCustomerGroupRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
    description: z.string(),
    customers: z.array(z.number().int()),
  })
  .partial()
  .passthrough();
const CustomerTypeEnum = z.enum(["individual", "company", "agent", "supplier"]);
const PreferredContactEnum = z.enum(["email", "phone", "sms"]);
const Customer = z
  .object({
    id: z.number().int(),
    phone: z.string().max(20).optional(),
    identification_number: z.string().min(10).max(20),
    first_name: z.string().max(100).optional(),
    last_name: z.string().max(100).optional(),
    email: z.string().max(254).email().optional(),
    customer_type: CustomerTypeEnum.optional(),
    is_vip: z.boolean().nullish(),
    accepts_marketing: z.boolean().optional(),
    registration_number: z.string().max(50).nullish(),
    tax_number: z.string().max(50).nullish(),
    preferred_contact: PreferredContactEnum.optional(),
    website: z.string().max(200).url().nullish(),
    description: z.string().nullish(),
    address_line1: z.string().max(200).optional(),
    address_line2: z.string().max(200).optional(),
    city: z.string().max(100).optional(),
    postal_code: z.string().max(20).optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
  })
  .passthrough();
const PaginatedCustomerList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Customer),
  })
  .passthrough();
const CustomerRequest = z
  .object({
    phone: z.string().max(20).optional(),
    identification_number: z.string().min(10).max(20),
    first_name: z.string().max(100).optional(),
    last_name: z.string().max(100).optional(),
    email: z.string().max(254).email().optional(),
    customer_type: CustomerTypeEnum.optional(),
    is_vip: z.boolean().nullish(),
    accepts_marketing: z.boolean().optional(),
    registration_number: z.string().max(50).nullish(),
    tax_number: z.string().max(50).nullish(),
    preferred_contact: PreferredContactEnum.optional(),
    website: z.string().max(200).url().nullish(),
    description: z.string().nullish(),
    address_line1: z.string().max(200).optional(),
    address_line2: z.string().max(200).optional(),
    city: z.string().max(100).optional(),
    postal_code: z.string().max(20).optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
  })
  .passthrough();
const PatchedCustomerRequest = z
  .object({
    phone: z.string().max(20),
    identification_number: z.string().min(10).max(20),
    first_name: z.string().max(100),
    last_name: z.string().max(100),
    email: z.string().max(254).email(),
    customer_type: CustomerTypeEnum,
    is_vip: z.boolean().nullable(),
    accepts_marketing: z.boolean(),
    registration_number: z.string().max(50).nullable(),
    tax_number: z.string().max(50).nullable(),
    preferred_contact: PreferredContactEnum,
    website: z.string().max(200).url().nullable(),
    description: z.string().nullable(),
    address_line1: z.string().max(200),
    address_line2: z.string().max(200),
    city: z.string().max(100),
    postal_code: z.string().max(20),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
  })
  .partial()
  .passthrough();
const Document = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().max(255),
    file: z.string().url(),
    customer: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedDocumentList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Document),
  })
  .passthrough();
const DocumentRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().min(1).max(255),
    file: z.instanceof(File),
    customer: z.number().int().nullish(),
  })
  .passthrough();
const PatchedDocumentRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    title: z.string().min(1).max(255),
    file: z.instanceof(File),
    customer: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const InteractionTypeEnum = z.enum(["call", "email", "meeting"]);
const Interaction = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    interaction_type: InteractionTypeEnum,
    notes: z.string().nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PaginatedInteractionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Interaction),
  })
  .passthrough();
const InteractionRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    interaction_type: InteractionTypeEnum,
    notes: z.string().nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PatchedInteractionRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    interaction_type: InteractionTypeEnum,
    notes: z.string().nullable(),
    customer: z.number().int(),
  })
  .partial()
  .passthrough();
const StageEnum = z.enum([
  "lead",
  "qualified",
  "proposal",
  "negotiation",
  "won",
  "lost",
]);
const Opportunity = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().max(255),
    stage: StageEnum.optional(),
    amount: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PaginatedOpportunityList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Opportunity),
  })
  .passthrough();
const OpportunityRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().min(1).max(255),
    stage: StageEnum.optional(),
    amount: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PatchedOpportunityRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    title: z.string().min(1).max(255),
    stage: StageEnum,
    amount: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullable(),
    customer: z.number().int(),
  })
  .partial()
  .passthrough();
const SubscriptionTypeEnum = z.enum(["monthly", "yearly", "lifetime"]);
const Subscription = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    subscription_type: SubscriptionTypeEnum,
    start_date: z.string().datetime({ offset: true }),
    end_date: z.string().datetime({ offset: true }),
    customer: z.number().int(),
  })
  .passthrough();
const PaginatedSubscriptionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Subscription),
  })
  .passthrough();
const SubscriptionRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    subscription_type: SubscriptionTypeEnum,
    end_date: z.string().datetime({ offset: true }),
    customer: z.number().int(),
  })
  .passthrough();
const PatchedSubscriptionRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    subscription_type: SubscriptionTypeEnum,
    end_date: z.string().datetime({ offset: true }),
    customer: z.number().int(),
  })
  .partial()
  .passthrough();
const PriorityEnum = z.enum(["low", "medium", "high"]);
const Task = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().max(255),
    description: z.string().nullish(),
    priority: PriorityEnum.optional(),
    due_date: z.string().datetime({ offset: true }).nullish(),
    completed: z.boolean().optional(),
    customer: z.number().int().nullish(),
    opportunity: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedTaskList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Task),
  })
  .passthrough();
const TaskRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().min(1).max(255),
    description: z.string().nullish(),
    priority: PriorityEnum.optional(),
    due_date: z.string().datetime({ offset: true }).nullish(),
    completed: z.boolean().optional(),
    customer: z.number().int().nullish(),
    opportunity: z.number().int().nullish(),
  })
  .passthrough();
const PatchedTaskRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    title: z.string().min(1).max(255),
    description: z.string().nullable(),
    priority: PriorityEnum,
    due_date: z.string().datetime({ offset: true }).nullable(),
    completed: z.boolean(),
    customer: z.number().int().nullable(),
    opportunity: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const Attendance = z
  .object({
    id: z.number().int(),
    date: z.string(),
    hours_worked: z.number().nullish(),
    check_in: z.string().nullish(),
    check_out: z.string().nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PaginatedAttendanceList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Attendance),
  })
  .passthrough();
const AttendanceRequest = z
  .object({
    date: z.string(),
    hours_worked: z.number().nullish(),
    check_in: z.string().nullish(),
    check_out: z.string().nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PatchedAttendanceRequest = z
  .object({
    date: z.string(),
    hours_worked: z.number().nullable(),
    check_in: z.string().nullable(),
    check_out: z.string().nullable(),
    employee: z.number().int(),
  })
  .partial()
  .passthrough();
const Department = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
    description: z.string().nullish(),
    location: z.string().max(100).nullish(),
  })
  .passthrough();
const PaginatedDepartmentList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Department),
  })
  .passthrough();
const DepartmentRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
    description: z.string().nullish(),
    location: z.string().max(100).nullish(),
  })
  .passthrough();
const PatchedDepartmentRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
    description: z.string().nullable(),
    location: z.string().max(100).nullable(),
  })
  .partial()
  .passthrough();
const PositionEnum = z.enum([
  "manager",
  "employee",
  "hr",
  "admin",
  "accountant",
  "marketing",
  "sales",
  "delivery",
  "customer_service",
]);
const Employee = z
  .object({
    id: z.number().int(),
    user_id: z.number().int(),
    department_id: z.number().int().nullish(),
    user_name: z.string(),
    department_name: z.string(),
    position: PositionEnum.optional(),
    salary: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    phone: z.string().max(20).optional(),
    hire_date: z.string().optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const PaginatedEmployeeList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Employee),
  })
  .passthrough();
const EmployeeRequest = z
  .object({
    user_id: z.number().int(),
    department_id: z.number().int().nullish(),
    position: PositionEnum.optional(),
    salary: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    phone: z.string().max(20).optional(),
    hire_date: z.string().optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
  })
  .passthrough();
const PatchedEmployeeRequest = z
  .object({
    user_id: z.number().int(),
    department_id: z.number().int().nullable(),
    position: PositionEnum,
    salary: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    phone: z.string().max(20),
    hire_date: z.string(),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
  })
  .partial()
  .passthrough();
const LeaveTypeEnum = z.enum(["sick", "vacation", "personal"]);
const LeaveStatusEnum = z.enum(["pending", "approved", "rejected"]);
const Leave = z
  .object({
    id: z.number().int(),
    leave_type: LeaveTypeEnum,
    start_date: z.string(),
    end_date: z.string().nullish(),
    status: LeaveStatusEnum.optional(),
    employee: z.number().int(),
  })
  .passthrough();
const PaginatedLeaveList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Leave),
  })
  .passthrough();
const LeaveRequest = z
  .object({
    leave_type: LeaveTypeEnum,
    end_date: z.string().nullish(),
    status: LeaveStatusEnum.optional(),
    employee: z.number().int(),
  })
  .passthrough();
const PatchedLeaveRequest = z
  .object({
    leave_type: LeaveTypeEnum,
    end_date: z.string().nullable(),
    status: LeaveStatusEnum,
    employee: z.number().int(),
  })
  .partial()
  .passthrough();
const NotificationTypeEnum = z.enum(["leave", "task", "payroll"]);
const Notification = z
  .object({
    id: z.number().int(),
    notification_type: NotificationTypeEnum,
    message: z.string().nullish(),
    is_read: z.boolean().optional(),
    created_at: z.string().datetime({ offset: true }),
    employee: z.number().int(),
  })
  .passthrough();
const PaginatedNotificationList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Notification),
  })
  .passthrough();
const NotificationRequest = z
  .object({
    notification_type: NotificationTypeEnum,
    message: z.string().nullish(),
    is_read: z.boolean().optional(),
    employee: z.number().int(),
  })
  .passthrough();
const PatchedNotificationRequest = z
  .object({
    notification_type: NotificationTypeEnum,
    message: z.string().nullable(),
    is_read: z.boolean(),
    employee: z.number().int(),
  })
  .partial()
  .passthrough();
const Payroll = z
  .object({
    id: z.number().int(),
    month: z.string().max(20),
    basic_salary: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    bonuses: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    deductions: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    net_salary: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PaginatedPayrollList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Payroll),
  })
  .passthrough();
const PayrollRequest = z
  .object({
    month: z.string().min(1).max(20),
    basic_salary: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    bonuses: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    deductions: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    net_salary: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PatchedPayrollRequest = z
  .object({
    month: z.string().min(1).max(20),
    basic_salary: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    bonuses: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    deductions: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    net_salary: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullable(),
    employee: z.number().int(),
  })
  .partial()
  .passthrough();
const RatingEnum = z.union([
  z.literal(1),
  z.literal(2),
  z.literal(3),
  z.literal(4),
  z.literal(5),
]);
const PerformanceReview = z
  .object({
    id: z.number().int(),
    review_date: z.string(),
    rating: RatingEnum,
    comments: z.string().nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PaginatedPerformanceReviewList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(PerformanceReview),
  })
  .passthrough();
const PerformanceReviewRequest = z
  .object({
    rating: RatingEnum,
    comments: z.string().nullish(),
    employee: z.number().int(),
  })
  .passthrough();
const PatchedPerformanceReviewRequest = z
  .object({
    rating: RatingEnum,
    comments: z.string().nullable(),
    employee: z.number().int(),
  })
  .partial()
  .passthrough();
const Permission = z
  .object({
    id: z.number().int(),
    code: z.string().max(100),
    description: z.string().optional(),
  })
  .passthrough();
const Role = z
  .object({
    id: z.number().int(),
    name: z.string().max(50),
    permissions: z.array(Permission),
  })
  .passthrough();
const User = z
  .object({
    id: z.number().int(),
    username: z.string().min(5).max(50),
    email: z.string().email(),
    first_name: z.string().max(30),
    last_name: z.string().max(30),
    role_id: z.number().int().nullish(),
    is_active: z.boolean().optional(),
    is_staff: z.boolean().optional(),
    role: Role,
    is_deleted: z.boolean().optional(),
    deleted_at: z.string().datetime({ offset: true }).nullable(),
    phone: z.string().regex(/^\+?\d{7,15}$/),
    client: z.number().int().nullable(),
  })
  .passthrough();
const RightSphereEnum = z.enum([
  "-30.00",
  "-29.75",
  "-29.50",
  "-29.25",
  "-29.00",
  "-28.75",
  "-28.50",
  "-28.25",
  "-28.00",
  "-27.75",
  "-27.50",
  "-27.25",
  "-27.00",
  "-26.75",
  "-26.50",
  "-26.25",
  "-26.00",
  "-25.75",
  "-25.50",
  "-25.25",
  "-25.00",
  "-24.75",
  "-24.50",
  "-24.25",
  "-24.00",
  "-23.75",
  "-23.50",
  "-23.25",
  "-23.00",
  "-22.75",
  "-22.50",
  "-22.25",
  "-22.00",
  "-21.75",
  "-21.50",
  "-21.25",
  "-21.00",
  "-20.75",
  "-20.50",
  "-20.25",
  "-20.00",
  "-19.75",
  "-19.50",
  "-19.25",
  "-19.00",
  "-18.75",
  "-18.50",
  "-18.25",
  "-18.00",
  "-17.75",
  "-17.50",
  "-17.25",
  "-17.00",
  "-16.75",
  "-16.50",
  "-16.25",
  "-16.00",
  "-15.75",
  "-15.50",
  "-15.25",
  "-15.00",
  "-14.75",
  "-14.50",
  "-14.25",
  "-14.00",
  "-13.75",
  "-13.50",
  "-13.25",
  "-13.00",
  "-12.75",
  "-12.50",
  "-12.25",
  "-12.00",
  "-11.75",
  "-11.50",
  "-11.25",
  "-11.00",
  "-10.75",
  "-10.50",
  "-10.25",
  "-10.00",
  "-09.75",
  "-09.50",
  "-09.25",
  "-09.00",
  "-08.75",
  "-08.50",
  "-08.25",
  "-08.00",
  "-07.75",
  "-07.50",
  "-07.25",
  "-07.00",
  "-06.75",
  "-06.50",
  "-06.25",
  "-06.00",
  "-05.75",
  "-05.50",
  "-05.25",
  "-05.00",
  "-04.75",
  "-04.50",
  "-04.25",
  "-04.00",
  "-03.75",
  "-03.50",
  "-03.25",
  "-03.00",
  "-02.75",
  "-02.50",
  "-02.25",
  "-02.00",
  "-01.75",
  "-01.50",
  "-01.25",
  "-01.00",
  "-00.75",
  "-00.50",
  "-00.25",
  "-00.00",
  "+00.25",
  "+00.50",
  "+00.75",
  "+01.00",
  "+01.25",
  "+01.50",
  "+01.75",
  "+02.00",
  "+02.25",
  "+02.50",
  "+02.75",
  "+03.00",
  "+03.25",
  "+03.50",
  "+03.75",
  "+04.00",
  "+04.25",
  "+04.50",
  "+04.75",
  "+05.00",
  "+05.25",
  "+05.50",
  "+05.75",
  "+06.00",
  "+06.25",
  "+06.50",
  "+06.75",
  "+07.00",
  "+07.25",
  "+07.50",
  "+07.75",
  "+08.00",
  "+08.25",
  "+08.50",
  "+08.75",
  "+09.00",
  "+09.25",
  "+09.50",
  "+09.75",
  "+10.00",
  "+10.25",
  "+10.50",
  "+10.75",
  "+11.00",
  "+11.25",
  "+11.50",
  "+11.75",
  "+12.00",
  "+12.25",
  "+12.50",
  "+12.75",
  "+13.00",
  "+13.25",
  "+13.50",
  "+13.75",
  "+14.00",
  "+14.25",
  "+14.50",
  "+14.75",
  "+15.00",
  "+15.25",
  "+15.50",
  "+15.75",
  "+16.00",
  "+16.25",
  "+16.50",
  "+16.75",
  "+17.00",
  "+17.25",
  "+17.50",
  "+17.75",
  "+18.00",
  "+18.25",
  "+18.50",
  "+18.75",
  "+19.00",
  "+19.25",
  "+19.50",
  "+19.75",
  "+20.00",
  "+20.25",
  "+20.50",
  "+20.75",
  "+21.00",
  "+21.25",
  "+21.50",
  "+21.75",
  "+22.00",
  "+22.25",
  "+22.50",
  "+22.75",
  "+23.00",
  "+23.25",
  "+23.50",
  "+23.75",
  "+24.00",
  "+24.25",
  "+24.50",
  "+24.75",
  "+25.00",
  "+25.25",
  "+25.50",
  "+25.75",
  "+26.00",
  "+26.25",
  "+26.50",
  "+26.75",
  "+27.00",
  "+27.25",
  "+27.50",
  "+27.75",
  "+28.00",
  "+28.25",
  "+28.50",
  "+28.75",
  "+29.00",
  "+29.25",
  "+29.50",
  "+29.75",
  "+30.00",
]);
const BlankEnum = z.unknown();
const NullEnum = z.unknown();
const RightCylinderEnum = z.enum([
  "-15.00",
  "-14.75",
  "-14.50",
  "-14.25",
  "-14.00",
  "-13.75",
  "-13.50",
  "-13.25",
  "-13.00",
  "-12.75",
  "-12.50",
  "-12.25",
  "-12.00",
  "-11.75",
  "-11.50",
  "-11.25",
  "-11.00",
  "-10.75",
  "-10.50",
  "-10.25",
  "-10.00",
  "-09.75",
  "-09.50",
  "-09.25",
  "-09.00",
  "-08.75",
  "-08.50",
  "-08.25",
  "-08.00",
  "-07.75",
  "-07.50",
  "-07.25",
  "-07.00",
  "-06.75",
  "-06.50",
  "-06.25",
  "-06.00",
  "-05.75",
  "-05.50",
  "-05.25",
  "-05.00",
  "-04.75",
  "-04.50",
  "-04.25",
  "-04.00",
  "-03.75",
  "-03.50",
  "-03.25",
  "-03.00",
  "-02.75",
  "-02.50",
  "-02.25",
  "-02.00",
  "-01.75",
  "-01.50",
  "-01.25",
  "-01.00",
  "-00.75",
  "-00.50",
  "-00.25",
  "-00.00",
]);
const LeftSphereEnum = z.enum([
  "-30.00",
  "-29.75",
  "-29.50",
  "-29.25",
  "-29.00",
  "-28.75",
  "-28.50",
  "-28.25",
  "-28.00",
  "-27.75",
  "-27.50",
  "-27.25",
  "-27.00",
  "-26.75",
  "-26.50",
  "-26.25",
  "-26.00",
  "-25.75",
  "-25.50",
  "-25.25",
  "-25.00",
  "-24.75",
  "-24.50",
  "-24.25",
  "-24.00",
  "-23.75",
  "-23.50",
  "-23.25",
  "-23.00",
  "-22.75",
  "-22.50",
  "-22.25",
  "-22.00",
  "-21.75",
  "-21.50",
  "-21.25",
  "-21.00",
  "-20.75",
  "-20.50",
  "-20.25",
  "-20.00",
  "-19.75",
  "-19.50",
  "-19.25",
  "-19.00",
  "-18.75",
  "-18.50",
  "-18.25",
  "-18.00",
  "-17.75",
  "-17.50",
  "-17.25",
  "-17.00",
  "-16.75",
  "-16.50",
  "-16.25",
  "-16.00",
  "-15.75",
  "-15.50",
  "-15.25",
  "-15.00",
  "-14.75",
  "-14.50",
  "-14.25",
  "-14.00",
  "-13.75",
  "-13.50",
  "-13.25",
  "-13.00",
  "-12.75",
  "-12.50",
  "-12.25",
  "-12.00",
  "-11.75",
  "-11.50",
  "-11.25",
  "-11.00",
  "-10.75",
  "-10.50",
  "-10.25",
  "-10.00",
  "-09.75",
  "-09.50",
  "-09.25",
  "-09.00",
  "-08.75",
  "-08.50",
  "-08.25",
  "-08.00",
  "-07.75",
  "-07.50",
  "-07.25",
  "-07.00",
  "-06.75",
  "-06.50",
  "-06.25",
  "-06.00",
  "-05.75",
  "-05.50",
  "-05.25",
  "-05.00",
  "-04.75",
  "-04.50",
  "-04.25",
  "-04.00",
  "-03.75",
  "-03.50",
  "-03.25",
  "-03.00",
  "-02.75",
  "-02.50",
  "-02.25",
  "-02.00",
  "-01.75",
  "-01.50",
  "-01.25",
  "-01.00",
  "-00.75",
  "-00.50",
  "-00.25",
  "-00.00",
  "+00.25",
  "+00.50",
  "+00.75",
  "+01.00",
  "+01.25",
  "+01.50",
  "+01.75",
  "+02.00",
  "+02.25",
  "+02.50",
  "+02.75",
  "+03.00",
  "+03.25",
  "+03.50",
  "+03.75",
  "+04.00",
  "+04.25",
  "+04.50",
  "+04.75",
  "+05.00",
  "+05.25",
  "+05.50",
  "+05.75",
  "+06.00",
  "+06.25",
  "+06.50",
  "+06.75",
  "+07.00",
  "+07.25",
  "+07.50",
  "+07.75",
  "+08.00",
  "+08.25",
  "+08.50",
  "+08.75",
  "+09.00",
  "+09.25",
  "+09.50",
  "+09.75",
  "+10.00",
  "+10.25",
  "+10.50",
  "+10.75",
  "+11.00",
  "+11.25",
  "+11.50",
  "+11.75",
  "+12.00",
  "+12.25",
  "+12.50",
  "+12.75",
  "+13.00",
  "+13.25",
  "+13.50",
  "+13.75",
  "+14.00",
  "+14.25",
  "+14.50",
  "+14.75",
  "+15.00",
  "+15.25",
  "+15.50",
  "+15.75",
  "+16.00",
  "+16.25",
  "+16.50",
  "+16.75",
  "+17.00",
  "+17.25",
  "+17.50",
  "+17.75",
  "+18.00",
  "+18.25",
  "+18.50",
  "+18.75",
  "+19.00",
  "+19.25",
  "+19.50",
  "+19.75",
  "+20.00",
  "+20.25",
  "+20.50",
  "+20.75",
  "+21.00",
  "+21.25",
  "+21.50",
  "+21.75",
  "+22.00",
  "+22.25",
  "+22.50",
  "+22.75",
  "+23.00",
  "+23.25",
  "+23.50",
  "+23.75",
  "+24.00",
  "+24.25",
  "+24.50",
  "+24.75",
  "+25.00",
  "+25.25",
  "+25.50",
  "+25.75",
  "+26.00",
  "+26.25",
  "+26.50",
  "+26.75",
  "+27.00",
  "+27.25",
  "+27.50",
  "+27.75",
  "+28.00",
  "+28.25",
  "+28.50",
  "+28.75",
  "+29.00",
  "+29.25",
  "+29.50",
  "+29.75",
  "+30.00",
]);
const LeftCylinderEnum = z.enum([
  "-15.00",
  "-14.75",
  "-14.50",
  "-14.25",
  "-14.00",
  "-13.75",
  "-13.50",
  "-13.25",
  "-13.00",
  "-12.75",
  "-12.50",
  "-12.25",
  "-12.00",
  "-11.75",
  "-11.50",
  "-11.25",
  "-11.00",
  "-10.75",
  "-10.50",
  "-10.25",
  "-10.00",
  "-09.75",
  "-09.50",
  "-09.25",
  "-09.00",
  "-08.75",
  "-08.50",
  "-08.25",
  "-08.00",
  "-07.75",
  "-07.50",
  "-07.25",
  "-07.00",
  "-06.75",
  "-06.50",
  "-06.25",
  "-06.00",
  "-05.75",
  "-05.50",
  "-05.25",
  "-05.00",
  "-04.75",
  "-04.50",
  "-04.25",
  "-04.00",
  "-03.75",
  "-03.50",
  "-03.25",
  "-03.00",
  "-02.75",
  "-02.50",
  "-02.25",
  "-02.00",
  "-01.75",
  "-01.50",
  "-01.25",
  "-01.00",
  "-00.75",
  "-00.50",
  "-00.25",
  "-00.00",
]);
const RightReadingAddEnum = z.enum([
  "+00.25",
  "+00.50",
  "+00.75",
  "+01.00",
  "+01.25",
  "+01.50",
  "+01.75",
  "+02.00",
  "+02.25",
  "+02.50",
  "+02.75",
  "+03.00",
  "+03.25",
  "+03.50",
  "+03.75",
  "+04.00",
  "+04.25",
  "+04.50",
  "+04.75",
  "+05.00",
  "+05.25",
  "+05.50",
  "+05.75",
  "+06.00",
]);
const LeftReadingAddEnum = z.enum([
  "+00.25",
  "+00.50",
  "+00.75",
  "+01.00",
  "+01.25",
  "+01.50",
  "+01.75",
  "+02.00",
  "+02.25",
  "+02.50",
  "+02.75",
  "+03.00",
  "+03.25",
  "+03.50",
  "+03.75",
  "+04.00",
  "+04.25",
  "+04.50",
  "+04.75",
  "+05.00",
  "+05.25",
  "+05.50",
  "+05.75",
  "+06.00",
]);
const PrescriptionRecord = z
  .object({
    id: z.number().int(),
    created_by: User,
    customer_name: z.string(),
    created_by_username: z.string(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    right_sphere: z.union([RightSphereEnum, BlankEnum, NullEnum]).nullish(),
    right_cylinder: z.union([RightCylinderEnum, BlankEnum, NullEnum]).nullish(),
    right_axis: z.number().gte(0).lte(180).nullish(),
    left_sphere: z.union([LeftSphereEnum, BlankEnum, NullEnum]).nullish(),
    left_cylinder: z.union([LeftCylinderEnum, BlankEnum, NullEnum]).nullish(),
    left_axis: z.number().gte(0).lte(180).nullish(),
    right_reading_add: z
      .union([RightReadingAddEnum, BlankEnum, NullEnum])
      .nullish(),
    left_reading_add: z
      .union([LeftReadingAddEnum, BlankEnum, NullEnum])
      .nullish(),
    right_pupillary_distance: z.number().nullish(),
    left_pupillary_distance: z.number().nullish(),
    sigmant_right: z.string().max(20).nullish(),
    sigmant_left: z.string().max(20).nullish(),
    a_v_right: z.string().max(20).nullish(),
    a_v_left: z.string().max(20).nullish(),
    vertical_distance_right: z.string().max(20).nullish(),
    vertical_distance_left: z.string().max(20).nullish(),
    notes: z.string().nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PaginatedPrescriptionRecordList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(PrescriptionRecord),
  })
  .passthrough();
const PrescriptionRecordRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    right_sphere: z.union([RightSphereEnum, BlankEnum, NullEnum]).nullish(),
    right_cylinder: z.union([RightCylinderEnum, BlankEnum, NullEnum]).nullish(),
    right_axis: z.number().gte(0).lte(180).nullish(),
    left_sphere: z.union([LeftSphereEnum, BlankEnum, NullEnum]).nullish(),
    left_cylinder: z.union([LeftCylinderEnum, BlankEnum, NullEnum]).nullish(),
    left_axis: z.number().gte(0).lte(180).nullish(),
    right_reading_add: z
      .union([RightReadingAddEnum, BlankEnum, NullEnum])
      .nullish(),
    left_reading_add: z
      .union([LeftReadingAddEnum, BlankEnum, NullEnum])
      .nullish(),
    right_pupillary_distance: z.number().nullish(),
    left_pupillary_distance: z.number().nullish(),
    sigmant_right: z.string().max(20).nullish(),
    sigmant_left: z.string().max(20).nullish(),
    a_v_right: z.string().max(20).nullish(),
    a_v_left: z.string().max(20).nullish(),
    vertical_distance_right: z.string().max(20).nullish(),
    vertical_distance_left: z.string().max(20).nullish(),
    notes: z.string().nullish(),
    customer: z.number().int(),
  })
  .passthrough();
const PatchedPrescriptionRecordRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    right_sphere: z.union([RightSphereEnum, BlankEnum, NullEnum]).nullable(),
    right_cylinder: z
      .union([RightCylinderEnum, BlankEnum, NullEnum])
      .nullable(),
    right_axis: z.number().gte(0).lte(180).nullable(),
    left_sphere: z.union([LeftSphereEnum, BlankEnum, NullEnum]).nullable(),
    left_cylinder: z.union([LeftCylinderEnum, BlankEnum, NullEnum]).nullable(),
    left_axis: z.number().gte(0).lte(180).nullable(),
    right_reading_add: z
      .union([RightReadingAddEnum, BlankEnum, NullEnum])
      .nullable(),
    left_reading_add: z
      .union([LeftReadingAddEnum, BlankEnum, NullEnum])
      .nullable(),
    right_pupillary_distance: z.number().nullable(),
    left_pupillary_distance: z.number().nullable(),
    sigmant_right: z.string().max(20).nullable(),
    sigmant_left: z.string().max(20).nullable(),
    a_v_right: z.string().max(20).nullable(),
    a_v_left: z.string().max(20).nullable(),
    vertical_distance_right: z.string().max(20).nullable(),
    vertical_distance_left: z.string().max(20).nullable(),
    notes: z.string().nullable(),
    customer: z.number().int(),
  })
  .partial()
  .passthrough();
const ProductVariantAnswer = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    answer: z.string(),
    question_id: z.number().int(),
    answered_by: z.number().int(),
  })
  .passthrough();
const PaginatedProductVariantAnswerList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariantAnswer),
  })
  .passthrough();
const ProductVariantAnswerRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    answer: z.string().min(1),
    question_id: z.number().int(),
    answered_by: z.number().int(),
  })
  .passthrough();
const PatchedProductVariantAnswerRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    answer: z.string().min(1),
    question_id: z.number().int(),
    answered_by: z.number().int(),
  })
  .partial()
  .passthrough();
const AttributeValue = z
  .object({
    id: z.number().int(),
    attribute_name: z.string(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    value: z.string().max(100),
    label: z.string().max(100).nullish(),
    unique_key: z.string(),
    attribute_id: z.number().int(),
  })
  .passthrough();
const PaginatedAttributeValueList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(AttributeValue),
  })
  .passthrough();
const AttributeValueRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    value: z.string().min(1).max(100),
    label: z.string().max(100).nullish(),
    attribute_id: z.number().int(),
  })
  .passthrough();
const PatchedAttributeValueRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    value: z.string().min(1).max(100),
    label: z.string().max(100).nullable(),
    attribute_id: z.number().int(),
  })
  .partial()
  .passthrough();
const Attributes = z
  .object({
    id: z.number().int(),
    values: z.array(AttributeValue),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
  })
  .passthrough();
const PaginatedAttributesList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Attributes),
  })
  .passthrough();
const AttributesRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
  })
  .passthrough();
const PatchedAttributesRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
  })
  .partial()
  .passthrough();
const ProductTypeEnum = z.enum(["CL", "SL", "FR", "AX", "OT", "DV", "All"]);
const Brand = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    description: z.string().optional(),
    product_type: ProductTypeEnum.optional(),
    logo: z.string().url().nullish(),
  })
  .passthrough();
const PaginatedBrandList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Brand),
  })
  .passthrough();
const BrandRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    description: z.string().optional(),
    product_type: ProductTypeEnum.optional(),
    logo: z.instanceof(File).nullish(),
  })
  .passthrough();
const PatchedBrandRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
    country: z.string().max(50),
    website: z.string().max(200).url(),
    description: z.string(),
    product_type: ProductTypeEnum,
    logo: z.instanceof(File).nullable(),
  })
  .partial()
  .passthrough();
const Category = z
  .object({
    id: z.number().int(),
    name: z.string().max(100),
    description: z.string().optional(),
    parent_id: z.number().int().nullish(),
    parent_name: z.string(),
    is_active: z.boolean().optional(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
  })
  .passthrough();
const PaginatedCategoryList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Category),
  })
  .passthrough();
const CategoryRequest = z
  .object({
    name: z.string().min(1).max(100),
    description: z.string().optional(),
    parent_id: z.number().int().nullish(),
    is_active: z.boolean().optional(),
  })
  .passthrough();
const PatchedCategoryRequest = z
  .object({
    name: z.string().min(1).max(100),
    description: z.string(),
    parent_id: z.number().int().nullable(),
    is_active: z.boolean(),
  })
  .partial()
  .passthrough();
const FlexiblePrice = z
  .object({
    id: z.number().int(),
    variant: z.number().int(),
    customer: z.number().int().nullable(),
    customer_group: CustomerGroup,
    branch: Branch,
    special_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    start_date: z.string().nullish(),
    end_date: z.string().nullish(),
    min_quantity: z.number().int().gte(0).lte(2147483647).optional(),
    currency: z.string().max(10).optional(),
    priority: z.number().int().gte(0).lte(2147483647).optional(),
  })
  .passthrough();
const PaginatedFlexiblePriceList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(FlexiblePrice),
  })
  .passthrough();
const FlexiblePriceRequest = z
  .object({
    variant: z.number().int(),
    customer: z.number().int().nullable(),
    customer_group_id: z.number().int().nullable(),
    branch_id: z.number().int().nullable(),
    special_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    start_date: z.string().nullish(),
    end_date: z.string().nullish(),
    min_quantity: z.number().int().gte(0).lte(2147483647).optional(),
    currency: z.string().min(1).max(10).optional(),
    priority: z.number().int().gte(0).lte(2147483647).optional(),
  })
  .passthrough();
const PatchedFlexiblePriceRequest = z
  .object({
    variant: z.number().int(),
    customer: z.number().int().nullable(),
    customer_group_id: z.number().int().nullable(),
    branch_id: z.number().int().nullable(),
    special_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    start_date: z.string().nullable(),
    end_date: z.string().nullable(),
    min_quantity: z.number().int().gte(0).lte(2147483647),
    currency: z.string().min(1).max(10),
    priority: z.number().int().gte(0).lte(2147483647),
  })
  .partial()
  .passthrough();
const Manufacturer = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(100),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    email: z.string().max(254).email().optional(),
    phone: z.string().max(20).optional(),
  })
  .passthrough();
const PaginatedManufacturerList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Manufacturer),
  })
  .passthrough();
const ManufacturerRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(100),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    email: z.string().max(254).email().optional(),
    phone: z.string().max(20).optional(),
  })
  .passthrough();
const PatchedManufacturerRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(100),
    country: z.string().max(50),
    website: z.string().max(200).url(),
    email: z.string().max(254).email(),
    phone: z.string().max(20),
  })
  .partial()
  .passthrough();
const GenderEnum = z.enum(["unisex", "men", "women", "kids"]);
const AgeGroupEnum = z.enum(["adult", "child", "senior"]);
const ProductVariantMarketing = z
  .object({
    id: z.number().int(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().max(200),
    description: z.string(),
    meta_title: z.string().max(200).optional(),
    meta_description: z.string().max(300).optional(),
    meta_keywords: z.string().max(200).optional(),
    slug: z
      .string()
      .max(50)
      .regex(/^[-a-zA-Z0-9_]+$/),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    seo_image: z.string().url().nullish(),
    seo_image_alt: z.string().max(200).optional(),
    gender: GenderEnum.optional(),
    age_group: z.union([AgeGroupEnum, BlankEnum]).optional(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PaginatedProductVariantMarketingList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariantMarketing),
  })
  .passthrough();
const ProductVariantMarketingRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    title: z.string().min(1).max(200),
    description: z.string().min(1),
    meta_title: z.string().max(200).optional(),
    meta_description: z.string().max(300).optional(),
    meta_keywords: z.string().max(200).optional(),
    slug: z
      .string()
      .min(1)
      .max(50)
      .regex(/^[-a-zA-Z0-9_]+$/),
    seo_image: z.instanceof(File).nullish(),
    seo_image_alt: z.string().max(200).optional(),
    gender: GenderEnum.optional(),
    age_group: z.union([AgeGroupEnum, BlankEnum]).optional(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PatchedProductVariantMarketingRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    title: z.string().min(1).max(200),
    description: z.string().min(1),
    meta_title: z.string().max(200),
    meta_description: z.string().max(300),
    meta_keywords: z.string().max(200),
    slug: z
      .string()
      .min(1)
      .max(50)
      .regex(/^[-a-zA-Z0-9_]+$/),
    seo_image: z.instanceof(File).nullable(),
    seo_image_alt: z.string().max(200),
    gender: GenderEnum,
    age_group: z.union([AgeGroupEnum, BlankEnum]),
    variant_id: z.number().int(),
  })
  .partial()
  .passthrough();
const ProductVariantOffer = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    offer: z.string().max(100),
    start_date: z.string(),
    end_date: z.string(),
    ProductVariant_id: z.number().int(),
  })
  .passthrough();
const PaginatedProductVariantOfferList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariantOffer),
  })
  .passthrough();
const ProductVariantOfferRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    offer: z.string().min(1).max(100),
    start_date: z.string(),
    end_date: z.string(),
    ProductVariant_id: z.number().int(),
  })
  .passthrough();
const PatchedProductVariantOfferRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    offer: z.string().min(1).max(100),
    start_date: z.string(),
    end_date: z.string(),
    ProductVariant_id: z.number().int(),
  })
  .partial()
  .passthrough();
const ProductImage = z
  .object({
    id: z.number().int(),
    variant_id: z.number().int(),
    image: z.string().url(),
    alt_text: z.string().max(200).optional(),
    order: z.number().int().gte(0).lte(2147483647).optional(),
    is_primary: z.boolean().optional(),
  })
  .passthrough();
const PaginatedProductImageList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductImage),
  })
  .passthrough();
const ProductImageRequest = z
  .object({
    variant_id: z.number().int(),
    image: z.instanceof(File),
    alt_text: z.string().max(200).optional(),
    order: z.number().int().gte(0).lte(2147483647).optional(),
    is_primary: z.boolean().optional(),
  })
  .passthrough();
const PatchedProductImageRequest = z
  .object({
    variant_id: z.number().int(),
    image: z.instanceof(File),
    alt_text: z.string().max(200),
    order: z.number().int().gte(0).lte(2147483647),
    is_primary: z.boolean(),
  })
  .partial()
  .passthrough();
const VariantTypeEnum = z.enum([
  "basic",
  "frames",
  "stockLenses",
  "rxLenses",
  "contactLenses",
  "custom",
]);
const Product = z
  .object({
    id: z.number().int(),
    manufacturer_name: z.string(),
    category_name: z.string(),
    supplier_name: z.string(),
    brand_name: z.string(),
    type: z.string(),
    variants: z.string(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    model: z.string().max(50),
    name: z.string().max(200).nullish(),
    description: z.string(),
    usku: z.string(),
    variant_type: VariantTypeEnum.optional(),
    category: z.number().int(),
    supplier: z.number().int(),
    manufacturer: z.number().int(),
    brand: z.number().int(),
  })
  .passthrough();
const PaginatedProductList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Product),
  })
  .passthrough();
const ProductRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    model: z.string().min(1).max(50),
    name: z.string().max(200).nullish(),
    variant_type: VariantTypeEnum.optional(),
    category: z.number().int(),
    supplier: z.number().int(),
    manufacturer: z.number().int(),
    brand: z.number().int(),
  })
  .passthrough();
const PatchedProductRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    model: z.string().min(1).max(50),
    name: z.string().max(200).nullable(),
    variant_type: VariantTypeEnum,
    category: z.number().int(),
    supplier: z.number().int(),
    manufacturer: z.number().int(),
    brand: z.number().int(),
  })
  .partial()
  .passthrough();
const ProductVariantQuestion = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    question: z.string(),
    ProductVariant_id: z.number().int(),
    asked_by: z.number().int(),
  })
  .passthrough();
const PaginatedProductVariantQuestionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariantQuestion),
  })
  .passthrough();
const ProductVariantQuestionRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    question: z.string().min(1),
    ProductVariant_id: z.number().int(),
    asked_by: z.number().int(),
  })
  .passthrough();
const PatchedProductVariantQuestionRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    question: z.string().min(1),
    ProductVariant_id: z.number().int(),
    asked_by: z.number().int(),
  })
  .partial()
  .passthrough();
const ProductVariantReview = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    rating: z.number().int().gte(0).lte(32767),
    review: z.string(),
    ProductVariant_id: z.number().int(),
    reviewed_by: z.number().int(),
  })
  .passthrough();
const PaginatedProductVariantReviewList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariantReview),
  })
  .passthrough();
const ProductVariantReviewRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    rating: z.number().int().gte(0).lte(32767),
    review: z.string().min(1),
    ProductVariant_id: z.number().int(),
    reviewed_by: z.number().int(),
  })
  .passthrough();
const PatchedProductVariantReviewRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    rating: z.number().int().gte(0).lte(32767),
    review: z.string().min(1),
    ProductVariant_id: z.number().int(),
    reviewed_by: z.number().int(),
  })
  .partial()
  .passthrough();
const MovementTypeEnum = z.enum([
  "purchase",
  "sale",
  "transfer_in",
  "transfer_out",
  "adjustment",
  "damage",
  "return",
  "reserve",
  "release",
]);
const StockMovements = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    movement_type: MovementTypeEnum,
    quantity: z.number().int().gte(-2147483648).lte(2147483647),
    quantity_before: z.number().int().gte(0).lte(2147483647),
    quantity_after: z.number().int().gte(0).lte(2147483647),
    reference_number: z.string().max(50).optional(),
    notes: z.string().optional(),
    movement_date: z.string().datetime({ offset: true }),
    cost_per_unit: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    stocks_id: z.number().int(),
  })
  .passthrough();
const PaginatedStockMovementsList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(StockMovements),
  })
  .passthrough();
const StockMovementsRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    movement_type: MovementTypeEnum,
    quantity: z.number().int().gte(-2147483648).lte(2147483647),
    quantity_before: z.number().int().gte(0).lte(2147483647),
    quantity_after: z.number().int().gte(0).lte(2147483647),
    reference_number: z.string().max(50).optional(),
    notes: z.string().optional(),
    cost_per_unit: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    stocks_id: z.number().int(),
  })
  .passthrough();
const PatchedStockMovementsRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    movement_type: MovementTypeEnum,
    quantity: z.number().int().gte(-2147483648).lte(2147483647),
    quantity_before: z.number().int().gte(0).lte(2147483647),
    quantity_after: z.number().int().gte(0).lte(2147483647),
    reference_number: z.string().max(50),
    notes: z.string(),
    cost_per_unit: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    stocks_id: z.number().int(),
  })
  .partial()
  .passthrough();
const StockTransferItem = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity_requested: z.number().int().gte(0).lte(2147483647),
    quantity_sent: z.number().int().gte(0).lte(2147483647).optional(),
    quantity_received: z.number().int().gte(0).lte(2147483647).optional(),
    unit_cost: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    notes: z.string().optional(),
    transfer_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PaginatedStockTransferItemList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(StockTransferItem),
  })
  .passthrough();
const StockTransferItemRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity_requested: z.number().int().gte(0).lte(2147483647),
    quantity_sent: z.number().int().gte(0).lte(2147483647).optional(),
    quantity_received: z.number().int().gte(0).lte(2147483647).optional(),
    unit_cost: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    notes: z.string().optional(),
    transfer_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PatchedStockTransferItemRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    quantity_requested: z.number().int().gte(0).lte(2147483647),
    quantity_sent: z.number().int().gte(0).lte(2147483647),
    quantity_received: z.number().int().gte(0).lte(2147483647),
    unit_cost: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    notes: z.string(),
    transfer_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .partial()
  .passthrough();
const StockTransferStatusEnum = z.enum([
  "pending",
  "in_transit",
  "completed",
  "cancelled",
]);
const StockTransfer = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    transfer_number: z.string(),
    status: StockTransferStatusEnum.optional(),
    requested_by: z.string().max(100).optional(),
    approved_by: z.string().max(100).optional(),
    requested_date: z.string().datetime({ offset: true }),
    approved_date: z.string().datetime({ offset: true }).nullish(),
    shipped_date: z.string().datetime({ offset: true }).nullish(),
    received_date: z.string().datetime({ offset: true }).nullish(),
    notes: z.string().optional(),
    from_branch_id: z.number().int(),
    to_branch_id: z.number().int(),
  })
  .passthrough();
const PaginatedStockTransferList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(StockTransfer),
  })
  .passthrough();
const StockTransferRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    status: StockTransferStatusEnum.optional(),
    requested_by: z.string().max(100).optional(),
    approved_by: z.string().max(100).optional(),
    approved_date: z.string().datetime({ offset: true }).nullish(),
    shipped_date: z.string().datetime({ offset: true }).nullish(),
    received_date: z.string().datetime({ offset: true }).nullish(),
    notes: z.string().optional(),
    from_branch_id: z.number().int(),
    to_branch_id: z.number().int(),
  })
  .passthrough();
const PatchedStockTransferRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    status: StockTransferStatusEnum,
    requested_by: z.string().max(100),
    approved_by: z.string().max(100),
    approved_date: z.string().datetime({ offset: true }).nullable(),
    shipped_date: z.string().datetime({ offset: true }).nullable(),
    received_date: z.string().datetime({ offset: true }).nullable(),
    notes: z.string(),
    from_branch_id: z.number().int(),
    to_branch_id: z.number().int(),
  })
  .partial()
  .passthrough();
const Stocks = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity_in_stock: z.number().int().gte(0).lte(2147483647).optional(),
    reserved_quantity: z.number().int().gte(0).lte(2147483647).optional(),
    reorder_level: z.number().int().gte(0).lte(2147483647).optional(),
    max_stock_level: z.number().int().gte(0).lte(2147483647).optional(),
    min_stock_level: z.number().int().gte(0).lte(2147483647).optional(),
    average_cost: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    last_restocked: z.string().datetime({ offset: true }).nullish(),
    last_sale: z.string().datetime({ offset: true }).nullish(),
    allow_backorder: z.boolean().optional(),
    branch_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PaginatedStocksList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Stocks),
  })
  .passthrough();
const StocksRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity_in_stock: z.number().int().gte(0).lte(2147483647).optional(),
    reserved_quantity: z.number().int().gte(0).lte(2147483647).optional(),
    reorder_level: z.number().int().gte(0).lte(2147483647).optional(),
    max_stock_level: z.number().int().gte(0).lte(2147483647).optional(),
    min_stock_level: z.number().int().gte(0).lte(2147483647).optional(),
    average_cost: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    last_restocked: z.string().datetime({ offset: true }).nullish(),
    last_sale: z.string().datetime({ offset: true }).nullish(),
    allow_backorder: z.boolean().optional(),
    branch_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .passthrough();
const PatchedStocksRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    quantity_in_stock: z.number().int().gte(0).lte(2147483647),
    reserved_quantity: z.number().int().gte(0).lte(2147483647),
    reorder_level: z.number().int().gte(0).lte(2147483647),
    max_stock_level: z.number().int().gte(0).lte(2147483647),
    min_stock_level: z.number().int().gte(0).lte(2147483647),
    average_cost: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    last_restocked: z.string().datetime({ offset: true }).nullable(),
    last_sale: z.string().datetime({ offset: true }).nullable(),
    allow_backorder: z.boolean(),
    branch_id: z.number().int(),
    variant_id: z.number().int(),
  })
  .partial()
  .passthrough();
const Supplier = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().max(50),
    contact_person: z.string().max(100).optional(),
    email: z.string().max(254).email().optional(),
    phone: z.string().max(20).optional(),
    address: z.string().optional(),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    payment_terms: z.string().max(100).optional(),
  })
  .passthrough();
const PaginatedSupplierList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Supplier),
  })
  .passthrough();
const SupplierRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    name: z.string().min(1).max(50),
    contact_person: z.string().max(100).optional(),
    email: z.string().max(254).email().optional(),
    phone: z.string().max(20).optional(),
    address: z.string().optional(),
    country: z.string().max(50).optional(),
    website: z.string().max(200).url().optional(),
    payment_terms: z.string().max(100).optional(),
  })
  .passthrough();
const PatchedSupplierRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    name: z.string().min(1).max(50),
    contact_person: z.string().max(100),
    email: z.string().max(254).email(),
    phone: z.string().max(20),
    address: z.string(),
    country: z.string().max(50),
    website: z.string().max(200).url(),
    payment_terms: z.string().max(100),
  })
  .partial()
  .passthrough();
const ProductVariant = z
  .object({
    id: z.number().int(),
    product_name: z.string(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    sku: z.string().max(50).nullish(),
    usku: z.string(),
    last_purchase_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    selling_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    discount_percentage: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    product: z.number().int(),
    product_type: z.number().int(),
    warranty: z.number().int().nullish(),
    weight: z.number().int().nullish(),
    dimensions: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedProductVariantList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ProductVariant),
  })
  .passthrough();
const ProductVariantRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    sku: z.string().max(50).nullish(),
    last_purchase_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    selling_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    discount_percentage: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullish(),
    product: z.number().int(),
    product_type: z.number().int(),
    warranty: z.number().int().nullish(),
    weight: z.number().int().nullish(),
    dimensions: z.number().int().nullish(),
  })
  .passthrough();
const PatchedProductVariantRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    sku: z.string().max(50).nullable(),
    last_purchase_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullable(),
    selling_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    discount_percentage: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .nullable(),
    product: z.number().int(),
    product_type: z.number().int(),
    warranty: z.number().int().nullable(),
    weight: z.number().int().nullable(),
    dimensions: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const InvoiceItem = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity: z.number().int().gte(0).lte(2147483647).optional(),
    unit_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    total_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    product_variant: z.number().int().nullish(),
    invoice: z.number().int(),
  })
  .passthrough();
const InvoiceTypeEnum = z.enum([
  "purchase",
  "sale",
  "return_purchase",
  "return_sale",
]);
const InvoiceStatusEnum = z.enum([
  "draft",
  "paid",
  "partially_paid",
  "overdue",
  "confirmed",
]);
const Invoice = z
  .object({
    id: z.number().int(),
    items: z.array(InvoiceItem),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    subtotal: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    tax_rate: z
      .string()
      .regex(/^-?\d{0,1}(?:\.\d{0,4})?$/)
      .optional(),
    tax_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    discount_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    total_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    paid_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    invoice_number: z.string(),
    invoice_type: InvoiceTypeEnum.optional(),
    due_date: z.string().nullish(),
    status: InvoiceStatusEnum,
    notes: z.string().nullish(),
    branch: z.number().int().nullish(),
    customer: z.number().int(),
    created_by: z.number().int().nullable(),
    order: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedInvoiceList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Invoice),
  })
  .passthrough();
const InvoiceItemRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity: z.number().int().gte(0).lte(2147483647).optional(),
    unit_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    product_variant: z.number().int().nullish(),
    invoice: z.number().int(),
  })
  .passthrough();
const InvoiceRequest = z
  .object({
    items: z.array(InvoiceItemRequest),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    tax_rate: z
      .string()
      .regex(/^-?\d{0,1}(?:\.\d{0,4})?$/)
      .optional(),
    discount_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    paid_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    invoice_type: InvoiceTypeEnum.optional(),
    due_date: z.string().nullish(),
    notes: z.string().nullish(),
    branch: z.number().int().nullish(),
    customer: z.number().int(),
    order: z.number().int().nullish(),
  })
  .passthrough();
const PatchedInvoiceRequest = z
  .object({
    items: z.array(InvoiceItemRequest),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    tax_rate: z.string().regex(/^-?\d{0,1}(?:\.\d{0,4})?$/),
    discount_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    paid_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    invoice_type: InvoiceTypeEnum,
    due_date: z.string().nullable(),
    notes: z.string().nullable(),
    branch: z.number().int().nullable(),
    customer: z.number().int(),
    order: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const OrderItem = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity: z.number().int().gte(0).lte(2147483647).optional(),
    unit_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    total_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    product_variant: z.number().int().nullish(),
    order: z.number().int(),
    prescription: z.number().int().nullish(),
  })
  .passthrough();
const OrderTypeEnum = z.enum(["cash", "credit", "insurance"]);
const OrderStatusEnum = z.enum([
  "pending",
  "confirmed",
  "ready",
  "delivered",
  "cancelled",
]);
const PaymentStatusEnum = z.enum([
  "pending",
  "partial",
  "paid",
  "refunded",
  "disputed",
]);
const PaymentTypeEnum = z.enum(["cash", "credit", "insurance"]);
const Order = z
  .object({
    id: z.number().int(),
    items: z.array(OrderItem),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    subtotal: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    tax_rate: z
      .string()
      .regex(/^-?\d{0,1}(?:\.\d{0,4})?$/)
      .optional(),
    tax_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    discount_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    total_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    paid_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    order_type: OrderTypeEnum.optional(),
    order_number: z.string(),
    status: OrderStatusEnum.optional(),
    payment_status: PaymentStatusEnum.optional(),
    payment_type: PaymentTypeEnum.optional(),
    notes: z.string().optional(),
    internal_notes: z.string().optional(),
    confirmed_at: z.string().datetime({ offset: true }).nullable(),
    delivered_at: z.string().datetime({ offset: true }).nullable(),
    expected_delivery: z.string().datetime({ offset: true }).nullish(),
    branch: z.number().int().nullish(),
    customer: z.number().int(),
    sales_person: z.number().int().nullish(),
  })
  .passthrough();
const PaginatedOrderList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Order),
  })
  .passthrough();
const OrderItemRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    quantity: z.number().int().gte(0).lte(2147483647).optional(),
    unit_price: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    product_variant: z.number().int().nullish(),
    order: z.number().int(),
    prescription: z.number().int().nullish(),
  })
  .passthrough();
const OrderRequest = z
  .object({
    items: z.array(OrderItemRequest),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    tax_rate: z
      .string()
      .regex(/^-?\d{0,1}(?:\.\d{0,4})?$/)
      .optional(),
    discount_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    paid_amount: z
      .string()
      .regex(/^-?\d{0,10}(?:\.\d{0,2})?$/)
      .optional(),
    order_type: OrderTypeEnum.optional(),
    status: OrderStatusEnum.optional(),
    payment_status: PaymentStatusEnum.optional(),
    payment_type: PaymentTypeEnum.optional(),
    notes: z.string().optional(),
    internal_notes: z.string().optional(),
    expected_delivery: z.string().datetime({ offset: true }).nullish(),
    branch: z.number().int().nullish(),
    customer: z.number().int(),
    sales_person: z.number().int().nullish(),
  })
  .passthrough();
const PatchedOrderRequest = z
  .object({
    items: z.array(OrderItemRequest),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    tax_rate: z.string().regex(/^-?\d{0,1}(?:\.\d{0,4})?$/),
    discount_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    paid_amount: z.string().regex(/^-?\d{0,10}(?:\.\d{0,2})?$/),
    order_type: OrderTypeEnum,
    status: OrderStatusEnum,
    payment_status: PaymentStatusEnum,
    payment_type: PaymentTypeEnum,
    notes: z.string(),
    internal_notes: z.string(),
    expected_delivery: z.string().datetime({ offset: true }).nullable(),
    branch: z.number().int().nullable(),
    customer: z.number().int(),
    sales_person: z.number().int().nullable(),
  })
  .partial()
  .passthrough();
const PaymentMethodEnum = z.enum(["cash", "card"]);
const Payment = z
  .object({
    id: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    payment_method: PaymentMethodEnum,
    invoice: z.number().int(),
  })
  .passthrough();
const PaginatedPaymentList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Payment),
  })
  .passthrough();
const PaymentRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    payment_method: PaymentMethodEnum,
    invoice: z.number().int(),
  })
  .passthrough();
const PatchedPaymentRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    amount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    payment_method: PaymentMethodEnum,
    invoice: z.number().int(),
  })
  .partial()
  .passthrough();
const SubscriptionPlanCurrencyEnum = z.enum([
  "usd",
  "egp",
  "sar",
  "aud",
  "eur",
]);
const SubscriptionPlan = z
  .object({
    id: z.number().int(),
    name: z.string().max(50),
    duration_months: z.number().int().gte(0).lte(2147483647).optional(),
    duration_years: z.number().int().gte(0).lte(2147483647).optional(),
    max_users: z.number().int().gte(0).lte(2147483647).optional(),
    max_branches: z.number().int().gte(0).lte(2147483647).optional(),
    max_products: z.number().int().gte(0).lte(2147483647).optional(),
    month_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    year_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    currency: SubscriptionPlanCurrencyEnum.optional(),
    discount: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    field_labels: z.string(),
  })
  .passthrough();
const Client = z
  .object({
    id: z.number().int(),
    name: z.string().max(100),
    max_users: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    max_products: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    max_branches: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    paid_until: z.string().nullish(),
    on_trial: z.boolean().optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    uuid: z.string().uuid(),
    created_at: z.string().datetime({ offset: true }),
    plans: SubscriptionPlan,
    is_paid: z.string(),
    is_plan_expired: z.string(),
    field_labels: z.string(),
  })
  .passthrough();
const PaginatedClientList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Client),
  })
  .passthrough();
const ClientRequest = z
  .object({
    name: z.string().min(1).max(100),
    max_users: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    max_products: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    max_branches: z.number().int().gte(-2147483648).lte(2147483647).optional(),
    paid_until: z.string().nullish(),
    on_trial: z.boolean().optional(),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
  })
  .passthrough();
const PatchedClientRequest = z
  .object({
    name: z.string().min(1).max(100),
    max_users: z.number().int().gte(-2147483648).lte(2147483647),
    max_products: z.number().int().gte(-2147483648).lte(2147483647),
    max_branches: z.number().int().gte(-2147483648).lte(2147483647),
    paid_until: z.string().nullable(),
    on_trial: z.boolean(),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
  })
  .partial()
  .passthrough();
const RegisterTenant = z
  .object({ name: z.string().max(25), email: z.string().email() })
  .passthrough();
const PaginatedRegisterTenantList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(RegisterTenant),
  })
  .passthrough();
const RegisterTenantRequest = z
  .object({
    name: z.string().min(1).max(25),
    email: z.string().min(1).email(),
    password: z
      .string()
      .min(8)
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/),
  })
  .passthrough();
const PatchedRegisterTenantRequest = z
  .object({
    name: z.string().min(1).max(25),
    email: z.string().min(1).email(),
    password: z
      .string()
      .min(8)
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/),
  })
  .partial()
  .passthrough();
const PaginatedSubscriptionPlanList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(SubscriptionPlan),
  })
  .passthrough();
const SubscriptionPlanRequest = z
  .object({
    name: z.string().min(1).max(50),
    duration_months: z.number().int().gte(0).lte(2147483647).optional(),
    duration_years: z.number().int().gte(0).lte(2147483647).optional(),
    max_users: z.number().int().gte(0).lte(2147483647).optional(),
    max_branches: z.number().int().gte(0).lte(2147483647).optional(),
    max_products: z.number().int().gte(0).lte(2147483647).optional(),
    month_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    year_price: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
    currency: SubscriptionPlanCurrencyEnum.optional(),
    discount: z
      .string()
      .regex(/^-?\d{0,8}(?:\.\d{0,2})?$/)
      .optional(),
  })
  .passthrough();
const PatchedSubscriptionPlanRequest = z
  .object({
    name: z.string().min(1).max(50),
    duration_months: z.number().int().gte(0).lte(2147483647),
    duration_years: z.number().int().gte(0).lte(2147483647),
    max_users: z.number().int().gte(0).lte(2147483647),
    max_branches: z.number().int().gte(0).lte(2147483647),
    max_products: z.number().int().gte(0).lte(2147483647),
    month_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    year_price: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
    currency: SubscriptionPlanCurrencyEnum,
    discount: z.string().regex(/^-?\d{0,8}(?:\.\d{0,2})?$/),
  })
  .partial()
  .passthrough();
const ContactUs = z
  .object({
    email: z.string().max(254).email(),
    phone: z.string().max(20),
    name: z.string().max(100),
    message: z.string().max(500),
  })
  .passthrough();
const PaginatedContactUsList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(ContactUs),
  })
  .passthrough();
const ContactUsRequest = z
  .object({
    email: z.string().min(1).max(254).email(),
    phone: z.string().min(1).max(20),
    name: z.string().min(1).max(100),
    message: z.string().min(1).max(500),
  })
  .passthrough();
const PatchedContactUsRequest = z
  .object({
    email: z.string().min(1).max(254).email(),
    phone: z.string().min(1).max(20),
    name: z.string().min(1).max(100),
    message: z.string().min(1).max(500),
  })
  .partial()
  .passthrough();
const LoginRequest = z
  .object({ username: z.string().min(1), password: z.string().min(1) })
  .passthrough();
const LoginSuccessResponse = z.object({ msg: z.string() }).passthrough();
const LoginBadRequest = z
  .object({ username: z.array(z.string()), password: z.array(z.string()) })
  .partial()
  .passthrough();
const LoginForbidden = z.object({ detail: z.string() }).passthrough();
const LogoutResponse = z.object({ msg: z.string() }).passthrough();
const TokenRefreshError = z.object({ error: z.string() }).passthrough();
const DefaultLanguageEnum = z.enum(["en", "ar"]);
const LanguageEnum = z.enum(["en", "ar"]);
const PageContent = z
  .object({
    language: LanguageEnum,
    title: z.string().max(200),
    content: z.string().optional(),
    seo_title: z.string().max(200).optional(),
    meta_description: z.string().max(500).optional(),
    meta_keywords: z.string().optional(),
  })
  .passthrough();
const Page = z
  .object({
    id: z.number().int(),
    default_language: DefaultLanguageEnum.optional(),
    is_published: z.boolean().optional(),
    slug: z
      .string()
      .max(200)
      .regex(/^[-a-zA-Z0-9_]+$/),
    is_deleted: z.boolean().optional(),
    is_active: z.boolean().optional(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    translations: z.array(PageContent),
  })
  .passthrough();
const PaginatedPageList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Page),
  })
  .passthrough();
const PageContentRequest = z
  .object({
    language: LanguageEnum,
    title: z.string().min(1).max(200),
    content: z.string().optional(),
    seo_title: z.string().max(200).optional(),
    meta_description: z.string().max(500).optional(),
    meta_keywords: z.string().optional(),
  })
  .passthrough();
const PageRequest = z
  .object({
    default_language: DefaultLanguageEnum.optional(),
    is_published: z.boolean().optional(),
    slug: z
      .string()
      .min(1)
      .max(200)
      .regex(/^[-a-zA-Z0-9_]+$/),
    is_deleted: z.boolean().optional(),
    is_active: z.boolean().optional(),
    translations: z.array(PageContentRequest),
  })
  .passthrough();
const PatchedPageRequest = z
  .object({
    default_language: DefaultLanguageEnum,
    is_published: z.boolean(),
    slug: z
      .string()
      .min(1)
      .max(200)
      .regex(/^[-a-zA-Z0-9_]+$/),
    is_deleted: z.boolean(),
    is_active: z.boolean(),
    translations: z.array(PageContentRequest),
  })
  .partial()
  .passthrough();
const PasswordResetSuccessResponse = z
  .object({ detail: z.string() })
  .passthrough();
const PasswordResetBadRequest = z
  .object({ email: z.array(z.string()) })
  .partial()
  .passthrough();
const PaginatedPermissionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Permission),
  })
  .passthrough();
const PermissionRequest = z
  .object({
    code: z.string().min(1).max(100),
    description: z.string().optional(),
  })
  .passthrough();
const PatchedPermissionRequest = z
  .object({ code: z.string().min(1).max(100), description: z.string() })
  .partial()
  .passthrough();
const Unauthorized = z.object({ error: z.string() }).passthrough();
const RegisterRequest = z
  .object({
    username: z.string().min(5).max(50),
    password: z
      .string()
      .min(8)
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/),
    email: z.string().min(1).email(),
  })
  .passthrough();
const RegisterSuccessResponse = z
  .object({ msg: z.string(), user: User })
  .passthrough();
const RolePermission = z
  .object({
    id: z.number().int(),
    role_name: z.string(),
    permission_name: z.string(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    role_id: z.number().int(),
    permission_id: z.number().int(),
  })
  .passthrough();
const PaginatedRolePermissionList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(RolePermission),
  })
  .passthrough();
const RolePermissionRequest = z
  .object({
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    role_id: z.number().int(),
    permission_id: z.number().int(),
  })
  .passthrough();
const PatchedRolePermissionRequest = z
  .object({
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    role_id: z.number().int(),
    permission_id: z.number().int(),
  })
  .partial()
  .passthrough();
const PaginatedRoleList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(Role),
  })
  .passthrough();
const RoleRequest = z.object({ name: z.string().min(1).max(50) }).passthrough();
const PatchedRoleRequest = z
  .object({ name: z.string().min(1).max(50) })
  .partial()
  .passthrough();
const TenantSettings = z
  .object({
    id: z.number().int(),
    logo: z.string().url().nullish(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.string().datetime({ offset: true }),
    is_active: z.boolean().optional(),
    is_deleted: z.boolean().optional(),
    business_name: z.string().max(255).optional(),
    description: z.string().optional(),
    facebook: z.string().max(200).url().optional(),
    instagram: z.string().max(200).url().optional(),
    whatsapp: z.string().max(20).optional(),
    twitter: z.string().max(200).url().optional(),
    tiktok: z.string().max(200).url().optional(),
    linkedin: z.string().max(200).url().optional(),
    phone: z.string().max(20).optional(),
    email: z.string().max(254).email().optional(),
    website: z.string().max(200).url().optional(),
    seo_title: z.string().max(255).optional(),
    seo_description: z.string().optional(),
    seo_keywords: z.string().max(255).optional(),
    address: z.string().max(255).optional(),
    city: z.string().max(100).optional(),
    state: z.string().max(100).optional(),
    postal_code: z.string().max(20).optional(),
    country: z.string().max(100).optional(),
    bank_name: z.string().max(100).optional(),
    account_number: z.string().max(100).optional(),
    iban: z.string().max(100).optional(),
    swift_code: z.string().max(100).optional(),
  })
  .passthrough();
const PaginatedTenantSettingsList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(TenantSettings),
  })
  .passthrough();
const TenantSettingsRequest = z
  .object({
    logo: z.instanceof(File).nullable(),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    business_name: z.string().min(1).max(255),
    description: z.string(),
    facebook: z.string().max(200).url(),
    instagram: z.string().max(200).url(),
    whatsapp: z.string().max(20),
    twitter: z.string().max(200).url(),
    tiktok: z.string().max(200).url(),
    linkedin: z.string().max(200).url(),
    phone: z.string().max(20),
    email: z.string().max(254).email(),
    website: z.string().max(200).url(),
    seo_title: z.string().max(255),
    seo_description: z.string(),
    seo_keywords: z.string().max(255),
    address: z.string().max(255),
    city: z.string().max(100),
    state: z.string().max(100),
    postal_code: z.string().max(20),
    country: z.string().max(100),
    bank_name: z.string().max(100),
    account_number: z.string().max(100),
    iban: z.string().max(100),
    swift_code: z.string().max(100),
  })
  .partial()
  .passthrough();
const PatchedTenantSettingsRequest = z
  .object({
    logo: z.instanceof(File).nullable(),
    is_active: z.boolean(),
    is_deleted: z.boolean(),
    business_name: z.string().min(1).max(255),
    description: z.string(),
    facebook: z.string().max(200).url(),
    instagram: z.string().max(200).url(),
    whatsapp: z.string().max(20),
    twitter: z.string().max(200).url(),
    tiktok: z.string().max(200).url(),
    linkedin: z.string().max(200).url(),
    phone: z.string().max(20),
    email: z.string().max(254).email(),
    website: z.string().max(200).url(),
    seo_title: z.string().max(255),
    seo_description: z.string(),
    seo_keywords: z.string().max(255),
    address: z.string().max(255),
    city: z.string().max(100),
    state: z.string().max(100),
    postal_code: z.string().max(20),
    country: z.string().max(100),
    bank_name: z.string().max(100),
    account_number: z.string().max(100),
    iban: z.string().max(100),
    swift_code: z.string().max(100),
  })
  .partial()
  .passthrough();
const RefreshTokenResponse = z
  .object({ msg: z.string(), access: z.string() })
  .passthrough();
const PaginatedUserList = z
  .object({
    count: z.number().int(),
    next: z.string().url().nullish(),
    previous: z.string().url().nullish(),
    results: z.array(User),
  })
  .passthrough();
const UserRequest = z
  .object({
    username: z.string().min(5).max(50),
    email: z.string().min(1).email(),
    first_name: z.string().min(1).max(30),
    last_name: z.string().min(1).max(30),
    role_id: z.number().int().nullish(),
    is_active: z.boolean().optional(),
    is_staff: z.boolean().optional(),
    password: z
      .string()
      .min(8)
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/),
    is_deleted: z.boolean().optional(),
    phone: z
      .string()
      .min(1)
      .regex(/^\+?\d{7,15}$/),
  })
  .passthrough();
const PatchedUserRequest = z
  .object({
    username: z.string().min(5).max(50),
    email: z.string().min(1).email(),
    first_name: z.string().min(1).max(30),
    last_name: z.string().min(1).max(30),
    role_id: z.number().int().nullable(),
    is_active: z.boolean(),
    is_staff: z.boolean(),
    password: z
      .string()
      .min(8)
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/),
    is_deleted: z.boolean(),
    phone: z
      .string()
      .min(1)
      .regex(/^\+?\d{7,15}$/),
  })
  .partial()
  .passthrough();

export const schemas = {
  AccountCurrencyEnum,
  Account,
  PaginatedAccountList,
  AccountRequest,
  PatchedAccountRequest,
  TransactionTypeEnum,
  AccountingCategory,
  PaginatedAccountingCategoryList,
  AccountingCategoryRequest,
  PatchedAccountingCategoryRequest,
  FinancialPeriod,
  PaginatedFinancialPeriodList,
  FinancialPeriodRequest,
  PatchedFinancialPeriodRequest,
  JournalEntry,
  PaginatedJournalEntryList,
  JournalEntryRequest,
  PatchedJournalEntryRequest,
  IntervalEnum,
  RecurringTransaction,
  PaginatedRecurringTransactionList,
  RecurringTransactionRequest,
  PatchedRecurringTransactionRequest,
  Tax,
  PaginatedTaxList,
  TaxRequest,
  PatchedTaxRequest,
  Transaction,
  PaginatedTransactionList,
  TransactionRequest,
  PatchedTransactionRequest,
  BranchUsers,
  PaginatedBranchUsersList,
  BranchUsersRequest,
  PatchedBranchUsersRequest,
  BranchTypeEnum,
  Branch,
  PaginatedBranchList,
  BranchRequest,
  PatchedBranchRequest,
  Campaign,
  PaginatedCampaignList,
  CampaignRequest,
  PatchedCampaignRequest,
  ComplaintStatusEnum,
  Complaint,
  PaginatedComplaintList,
  ComplaintRequest,
  PatchedComplaintRequest,
  Contact,
  PaginatedContactList,
  ContactRequest,
  PatchedContactRequest,
  CustomerGroup,
  PaginatedCustomerGroupList,
  CustomerGroupRequest,
  PatchedCustomerGroupRequest,
  CustomerTypeEnum,
  PreferredContactEnum,
  Customer,
  PaginatedCustomerList,
  CustomerRequest,
  PatchedCustomerRequest,
  Document,
  PaginatedDocumentList,
  DocumentRequest,
  PatchedDocumentRequest,
  InteractionTypeEnum,
  Interaction,
  PaginatedInteractionList,
  InteractionRequest,
  PatchedInteractionRequest,
  StageEnum,
  Opportunity,
  PaginatedOpportunityList,
  OpportunityRequest,
  PatchedOpportunityRequest,
  SubscriptionTypeEnum,
  Subscription,
  PaginatedSubscriptionList,
  SubscriptionRequest,
  PatchedSubscriptionRequest,
  PriorityEnum,
  Task,
  PaginatedTaskList,
  TaskRequest,
  PatchedTaskRequest,
  Attendance,
  PaginatedAttendanceList,
  AttendanceRequest,
  PatchedAttendanceRequest,
  Department,
  PaginatedDepartmentList,
  DepartmentRequest,
  PatchedDepartmentRequest,
  PositionEnum,
  Employee,
  PaginatedEmployeeList,
  EmployeeRequest,
  PatchedEmployeeRequest,
  LeaveTypeEnum,
  LeaveStatusEnum,
  Leave,
  PaginatedLeaveList,
  LeaveRequest,
  PatchedLeaveRequest,
  NotificationTypeEnum,
  Notification,
  PaginatedNotificationList,
  NotificationRequest,
  PatchedNotificationRequest,
  Payroll,
  PaginatedPayrollList,
  PayrollRequest,
  PatchedPayrollRequest,
  RatingEnum,
  PerformanceReview,
  PaginatedPerformanceReviewList,
  PerformanceReviewRequest,
  PatchedPerformanceReviewRequest,
  Permission,
  Role,
  User,
  RightSphereEnum,
  BlankEnum,
  NullEnum,
  RightCylinderEnum,
  LeftSphereEnum,
  LeftCylinderEnum,
  RightReadingAddEnum,
  LeftReadingAddEnum,
  PrescriptionRecord,
  PaginatedPrescriptionRecordList,
  PrescriptionRecordRequest,
  PatchedPrescriptionRecordRequest,
  ProductVariantAnswer,
  PaginatedProductVariantAnswerList,
  ProductVariantAnswerRequest,
  PatchedProductVariantAnswerRequest,
  AttributeValue,
  PaginatedAttributeValueList,
  AttributeValueRequest,
  PatchedAttributeValueRequest,
  Attributes,
  PaginatedAttributesList,
  AttributesRequest,
  PatchedAttributesRequest,
  ProductTypeEnum,
  Brand,
  PaginatedBrandList,
  BrandRequest,
  PatchedBrandRequest,
  Category,
  PaginatedCategoryList,
  CategoryRequest,
  PatchedCategoryRequest,
  FlexiblePrice,
  PaginatedFlexiblePriceList,
  FlexiblePriceRequest,
  PatchedFlexiblePriceRequest,
  Manufacturer,
  PaginatedManufacturerList,
  ManufacturerRequest,
  PatchedManufacturerRequest,
  GenderEnum,
  AgeGroupEnum,
  ProductVariantMarketing,
  PaginatedProductVariantMarketingList,
  ProductVariantMarketingRequest,
  PatchedProductVariantMarketingRequest,
  ProductVariantOffer,
  PaginatedProductVariantOfferList,
  ProductVariantOfferRequest,
  PatchedProductVariantOfferRequest,
  ProductImage,
  PaginatedProductImageList,
  ProductImageRequest,
  PatchedProductImageRequest,
  VariantTypeEnum,
  Product,
  PaginatedProductList,
  ProductRequest,
  PatchedProductRequest,
  ProductVariantQuestion,
  PaginatedProductVariantQuestionList,
  ProductVariantQuestionRequest,
  PatchedProductVariantQuestionRequest,
  ProductVariantReview,
  PaginatedProductVariantReviewList,
  ProductVariantReviewRequest,
  PatchedProductVariantReviewRequest,
  MovementTypeEnum,
  StockMovements,
  PaginatedStockMovementsList,
  StockMovementsRequest,
  PatchedStockMovementsRequest,
  StockTransferItem,
  PaginatedStockTransferItemList,
  StockTransferItemRequest,
  PatchedStockTransferItemRequest,
  StockTransferStatusEnum,
  StockTransfer,
  PaginatedStockTransferList,
  StockTransferRequest,
  PatchedStockTransferRequest,
  Stocks,
  PaginatedStocksList,
  StocksRequest,
  PatchedStocksRequest,
  Supplier,
  PaginatedSupplierList,
  SupplierRequest,
  PatchedSupplierRequest,
  ProductVariant,
  PaginatedProductVariantList,
  ProductVariantRequest,
  PatchedProductVariantRequest,
  InvoiceItem,
  InvoiceTypeEnum,
  InvoiceStatusEnum,
  Invoice,
  PaginatedInvoiceList,
  InvoiceItemRequest,
  InvoiceRequest,
  PatchedInvoiceRequest,
  OrderItem,
  OrderTypeEnum,
  OrderStatusEnum,
  PaymentStatusEnum,
  PaymentTypeEnum,
  Order,
  PaginatedOrderList,
  OrderItemRequest,
  OrderRequest,
  PatchedOrderRequest,
  PaymentMethodEnum,
  Payment,
  PaginatedPaymentList,
  PaymentRequest,
  PatchedPaymentRequest,
  SubscriptionPlanCurrencyEnum,
  SubscriptionPlan,
  Client,
  PaginatedClientList,
  ClientRequest,
  PatchedClientRequest,
  RegisterTenant,
  PaginatedRegisterTenantList,
  RegisterTenantRequest,
  PatchedRegisterTenantRequest,
  PaginatedSubscriptionPlanList,
  SubscriptionPlanRequest,
  PatchedSubscriptionPlanRequest,
  ContactUs,
  PaginatedContactUsList,
  ContactUsRequest,
  PatchedContactUsRequest,
  LoginRequest,
  LoginSuccessResponse,
  LoginBadRequest,
  LoginForbidden,
  LogoutResponse,
  TokenRefreshError,
  DefaultLanguageEnum,
  LanguageEnum,
  PageContent,
  Page,
  PaginatedPageList,
  PageContentRequest,
  PageRequest,
  PatchedPageRequest,
  PasswordResetSuccessResponse,
  PasswordResetBadRequest,
  PaginatedPermissionList,
  PermissionRequest,
  PatchedPermissionRequest,
  Unauthorized,
  RegisterRequest,
  RegisterSuccessResponse,
  RolePermission,
  PaginatedRolePermissionList,
  RolePermissionRequest,
  PatchedRolePermissionRequest,
  PaginatedRoleList,
  RoleRequest,
  PatchedRoleRequest,
  TenantSettings,
  PaginatedTenantSettingsList,
  TenantSettingsRequest,
  PatchedTenantSettingsRequest,
  RefreshTokenResponse,
  PaginatedUserList,
  UserRequest,
  PatchedUserRequest,
};

export const endpoints = makeApi([
  {
    method: "get",
    path: "/api/accounting/accounts/",
    alias: "accounting_accounts_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedAccountList,
  },
  {
    method: "post",
    path: "/api/accounting/accounts/",
    alias: "accounting_accounts_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AccountRequest,
      },
    ],
    response: Account,
  },
  {
    method: "get",
    path: "/api/accounting/accounts/:id/",
    alias: "accounting_accounts_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Account,
  },
  {
    method: "put",
    path: "/api/accounting/accounts/:id/",
    alias: "accounting_accounts_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AccountRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Account,
  },
  {
    method: "patch",
    path: "/api/accounting/accounts/:id/",
    alias: "accounting_accounts_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedAccountRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Account,
  },
  {
    method: "delete",
    path: "/api/accounting/accounts/:id/",
    alias: "accounting_accounts_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/categories/",
    alias: "accounting_categories_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedAccountingCategoryList,
  },
  {
    method: "post",
    path: "/api/accounting/categories/",
    alias: "accounting_categories_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AccountingCategoryRequest,
      },
    ],
    response: AccountingCategory,
  },
  {
    method: "get",
    path: "/api/accounting/categories/:id/",
    alias: "accounting_categories_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AccountingCategory,
  },
  {
    method: "put",
    path: "/api/accounting/categories/:id/",
    alias: "accounting_categories_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AccountingCategoryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AccountingCategory,
  },
  {
    method: "patch",
    path: "/api/accounting/categories/:id/",
    alias: "accounting_categories_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedAccountingCategoryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AccountingCategory,
  },
  {
    method: "delete",
    path: "/api/accounting/categories/:id/",
    alias: "accounting_categories_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/financial-periods/",
    alias: "accounting_financial_periods_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedFinancialPeriodList,
  },
  {
    method: "post",
    path: "/api/accounting/financial-periods/",
    alias: "accounting_financial_periods_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: FinancialPeriodRequest,
      },
    ],
    response: FinancialPeriod,
  },
  {
    method: "get",
    path: "/api/accounting/financial-periods/:id/",
    alias: "accounting_financial_periods_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FinancialPeriod,
  },
  {
    method: "put",
    path: "/api/accounting/financial-periods/:id/",
    alias: "accounting_financial_periods_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: FinancialPeriodRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FinancialPeriod,
  },
  {
    method: "patch",
    path: "/api/accounting/financial-periods/:id/",
    alias: "accounting_financial_periods_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedFinancialPeriodRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FinancialPeriod,
  },
  {
    method: "delete",
    path: "/api/accounting/financial-periods/:id/",
    alias: "accounting_financial_periods_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/journal-entries/",
    alias: "accounting_journal_entries_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedJournalEntryList,
  },
  {
    method: "post",
    path: "/api/accounting/journal-entries/",
    alias: "accounting_journal_entries_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: JournalEntryRequest,
      },
    ],
    response: JournalEntry,
  },
  {
    method: "get",
    path: "/api/accounting/journal-entries/:id/",
    alias: "accounting_journal_entries_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: JournalEntry,
  },
  {
    method: "put",
    path: "/api/accounting/journal-entries/:id/",
    alias: "accounting_journal_entries_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: JournalEntryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: JournalEntry,
  },
  {
    method: "patch",
    path: "/api/accounting/journal-entries/:id/",
    alias: "accounting_journal_entries_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedJournalEntryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: JournalEntry,
  },
  {
    method: "delete",
    path: "/api/accounting/journal-entries/:id/",
    alias: "accounting_journal_entries_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/recurring-transactions/",
    alias: "accounting_recurring_transactions_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedRecurringTransactionList,
  },
  {
    method: "post",
    path: "/api/accounting/recurring-transactions/",
    alias: "accounting_recurring_transactions_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RecurringTransactionRequest,
      },
    ],
    response: RecurringTransaction,
  },
  {
    method: "get",
    path: "/api/accounting/recurring-transactions/:id/",
    alias: "accounting_recurring_transactions_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RecurringTransaction,
  },
  {
    method: "put",
    path: "/api/accounting/recurring-transactions/:id/",
    alias: "accounting_recurring_transactions_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RecurringTransactionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RecurringTransaction,
  },
  {
    method: "patch",
    path: "/api/accounting/recurring-transactions/:id/",
    alias: "accounting_recurring_transactions_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedRecurringTransactionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RecurringTransaction,
  },
  {
    method: "delete",
    path: "/api/accounting/recurring-transactions/:id/",
    alias: "accounting_recurring_transactions_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/taxes/",
    alias: "accounting_taxes_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedTaxList,
  },
  {
    method: "post",
    path: "/api/accounting/taxes/",
    alias: "accounting_taxes_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaxRequest,
      },
    ],
    response: Tax,
  },
  {
    method: "get",
    path: "/api/accounting/taxes/:id/",
    alias: "accounting_taxes_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Tax,
  },
  {
    method: "put",
    path: "/api/accounting/taxes/:id/",
    alias: "accounting_taxes_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaxRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Tax,
  },
  {
    method: "patch",
    path: "/api/accounting/taxes/:id/",
    alias: "accounting_taxes_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedTaxRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Tax,
  },
  {
    method: "delete",
    path: "/api/accounting/taxes/:id/",
    alias: "accounting_taxes_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/accounting/transactions/",
    alias: "accounting_transactions_list",
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedTransactionList,
  },
  {
    method: "post",
    path: "/api/accounting/transactions/",
    alias: "accounting_transactions_create",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TransactionRequest,
      },
    ],
    response: Transaction,
  },
  {
    method: "get",
    path: "/api/accounting/transactions/:id/",
    alias: "accounting_transactions_retrieve",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Transaction,
  },
  {
    method: "put",
    path: "/api/accounting/transactions/:id/",
    alias: "accounting_transactions_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TransactionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Transaction,
  },
  {
    method: "patch",
    path: "/api/accounting/transactions/:id/",
    alias: "accounting_transactions_partial_update",
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedTransactionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Transaction,
  },
  {
    method: "delete",
    path: "/api/accounting/transactions/:id/",
    alias: "accounting_transactions_destroy",
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/branches/branch-users/",
    alias: "branches_branch_users_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "branch_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "employee_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedBranchUsersList,
  },
  {
    method: "post",
    path: "/api/branches/branch-users/",
    alias: "branches_branch_users_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BranchUsersRequest,
      },
    ],
    response: BranchUsers,
  },
  {
    method: "get",
    path: "/api/branches/branch-users/:id/",
    alias: "branches_branch_users_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: BranchUsers,
  },
  {
    method: "put",
    path: "/api/branches/branch-users/:id/",
    alias: "branches_branch_users_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BranchUsersRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: BranchUsers,
  },
  {
    method: "patch",
    path: "/api/branches/branch-users/:id/",
    alias: "branches_branch_users_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedBranchUsersRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: BranchUsers,
  },
  {
    method: "delete",
    path: "/api/branches/branch-users/:id/",
    alias: "branches_branch_users_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/branches/branch-users/filter_options/",
    alias: "branches_branch_users_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: BranchUsers,
  },
  {
    method: "get",
    path: "/api/branches/branches/",
    alias: "branches_branches_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "address",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "allows_online_orders",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "branch_code",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "branch_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "city",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "country",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_main_branch",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "operating_hours",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedBranchList,
  },
  {
    method: "post",
    path: "/api/branches/branches/",
    alias: "branches_branches_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BranchRequest,
      },
    ],
    response: Branch,
  },
  {
    method: "get",
    path: "/api/branches/branches/:id/",
    alias: "branches_branches_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Branch,
  },
  {
    method: "put",
    path: "/api/branches/branches/:id/",
    alias: "branches_branches_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BranchRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Branch,
  },
  {
    method: "patch",
    path: "/api/branches/branches/:id/",
    alias: "branches_branches_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedBranchRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Branch,
  },
  {
    method: "delete",
    path: "/api/branches/branches/:id/",
    alias: "branches_branches_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/branches/branches/filter_options/",
    alias: "branches_branches_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Branch,
  },
  {
    method: "post",
    path: "/api/core/import-csv/",
    alias: "core_import_csv_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/campaigns/",
    alias: "crm_campaigns_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customers",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "end_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "start_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedCampaignList,
  },
  {
    method: "post",
    path: "/api/crm/campaigns/",
    alias: "crm_campaigns_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CampaignRequest,
      },
    ],
    response: Campaign,
  },
  {
    method: "get",
    path: "/api/crm/campaigns/:id/",
    alias: "crm_campaigns_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Campaign,
  },
  {
    method: "put",
    path: "/api/crm/campaigns/:id/",
    alias: "crm_campaigns_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CampaignRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Campaign,
  },
  {
    method: "patch",
    path: "/api/crm/campaigns/:id/",
    alias: "crm_campaigns_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedCampaignRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Campaign,
  },
  {
    method: "delete",
    path: "/api/crm/campaigns/:id/",
    alias: "crm_campaigns_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/campaigns/filter_options/",
    alias: "crm_campaigns_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Campaign,
  },
  {
    method: "get",
    path: "/api/crm/complaints/",
    alias: "crm_complaints_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedComplaintList,
  },
  {
    method: "post",
    path: "/api/crm/complaints/",
    alias: "crm_complaints_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ComplaintRequest,
      },
    ],
    response: Complaint,
  },
  {
    method: "get",
    path: "/api/crm/complaints/:id/",
    alias: "crm_complaints_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Complaint,
  },
  {
    method: "put",
    path: "/api/crm/complaints/:id/",
    alias: "crm_complaints_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ComplaintRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Complaint,
  },
  {
    method: "patch",
    path: "/api/crm/complaints/:id/",
    alias: "crm_complaints_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedComplaintRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Complaint,
  },
  {
    method: "delete",
    path: "/api/crm/complaints/:id/",
    alias: "crm_complaints_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/complaints/filter_options/",
    alias: "crm_complaints_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Complaint,
  },
  {
    method: "get",
    path: "/api/crm/contact-us/",
    alias: "crm_contact_us_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "message",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedContactList,
  },
  {
    method: "post",
    path: "/api/crm/contact-us/",
    alias: "crm_contact_us_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ContactRequest,
      },
    ],
    response: Contact,
  },
  {
    method: "get",
    path: "/api/crm/contact-us/:id/",
    alias: "crm_contact_us_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Contact,
  },
  {
    method: "put",
    path: "/api/crm/contact-us/:id/",
    alias: "crm_contact_us_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ContactRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Contact,
  },
  {
    method: "patch",
    path: "/api/crm/contact-us/:id/",
    alias: "crm_contact_us_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedContactRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Contact,
  },
  {
    method: "delete",
    path: "/api/crm/contact-us/:id/",
    alias: "crm_contact_us_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/contact-us/filter_options/",
    alias: "crm_contact_us_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Contact,
  },
  {
    method: "get",
    path: "/api/crm/customer-groups/",
    alias: "crm_customer_groups_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customers",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedCustomerGroupList,
  },
  {
    method: "post",
    path: "/api/crm/customer-groups/",
    alias: "crm_customer_groups_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CustomerGroupRequest,
      },
    ],
    response: CustomerGroup,
  },
  {
    method: "get",
    path: "/api/crm/customer-groups/:id/",
    alias: "crm_customer_groups_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: CustomerGroup,
  },
  {
    method: "put",
    path: "/api/crm/customer-groups/:id/",
    alias: "crm_customer_groups_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CustomerGroupRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: CustomerGroup,
  },
  {
    method: "patch",
    path: "/api/crm/customer-groups/:id/",
    alias: "crm_customer_groups_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedCustomerGroupRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: CustomerGroup,
  },
  {
    method: "delete",
    path: "/api/crm/customer-groups/:id/",
    alias: "crm_customer_groups_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/customer-groups/filter_options/",
    alias: "crm_customer_groups_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: CustomerGroup,
  },
  {
    method: "get",
    path: "/api/crm/customers/",
    alias: "crm_customers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "customer_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "first_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "last_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedCustomerList,
  },
  {
    method: "post",
    path: "/api/crm/customers/",
    alias: "crm_customers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CustomerRequest,
      },
    ],
    response: Customer,
  },
  {
    method: "get",
    path: "/api/crm/customers/:id/",
    alias: "crm_customers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Customer,
  },
  {
    method: "put",
    path: "/api/crm/customers/:id/",
    alias: "crm_customers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CustomerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Customer,
  },
  {
    method: "patch",
    path: "/api/crm/customers/:id/",
    alias: "crm_customers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedCustomerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Customer,
  },
  {
    method: "delete",
    path: "/api/crm/customers/:id/",
    alias: "crm_customers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/customers/filter_options/",
    alias: "crm_customers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Customer,
  },
  {
    method: "get",
    path: "/api/crm/documents/",
    alias: "crm_documents_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "file",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedDocumentList,
  },
  {
    method: "post",
    path: "/api/crm/documents/",
    alias: "crm_documents_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: DocumentRequest,
      },
    ],
    response: Document,
  },
  {
    method: "get",
    path: "/api/crm/documents/:id/",
    alias: "crm_documents_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Document,
  },
  {
    method: "put",
    path: "/api/crm/documents/:id/",
    alias: "crm_documents_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: DocumentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Document,
  },
  {
    method: "patch",
    path: "/api/crm/documents/:id/",
    alias: "crm_documents_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedDocumentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Document,
  },
  {
    method: "delete",
    path: "/api/crm/documents/:id/",
    alias: "crm_documents_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/documents/filter_options/",
    alias: "crm_documents_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Document,
  },
  {
    method: "get",
    path: "/api/crm/interactions/",
    alias: "crm_interactions_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "interaction_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedInteractionList,
  },
  {
    method: "post",
    path: "/api/crm/interactions/",
    alias: "crm_interactions_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InteractionRequest,
      },
    ],
    response: Interaction,
  },
  {
    method: "get",
    path: "/api/crm/interactions/:id/",
    alias: "crm_interactions_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Interaction,
  },
  {
    method: "put",
    path: "/api/crm/interactions/:id/",
    alias: "crm_interactions_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InteractionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Interaction,
  },
  {
    method: "patch",
    path: "/api/crm/interactions/:id/",
    alias: "crm_interactions_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedInteractionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Interaction,
  },
  {
    method: "delete",
    path: "/api/crm/interactions/:id/",
    alias: "crm_interactions_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/interactions/filter_options/",
    alias: "crm_interactions_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Interaction,
  },
  {
    method: "get",
    path: "/api/crm/opportunities/",
    alias: "crm_opportunities_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "stage",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedOpportunityList,
  },
  {
    method: "post",
    path: "/api/crm/opportunities/",
    alias: "crm_opportunities_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OpportunityRequest,
      },
    ],
    response: Opportunity,
  },
  {
    method: "get",
    path: "/api/crm/opportunities/:id/",
    alias: "crm_opportunities_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Opportunity,
  },
  {
    method: "put",
    path: "/api/crm/opportunities/:id/",
    alias: "crm_opportunities_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OpportunityRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Opportunity,
  },
  {
    method: "patch",
    path: "/api/crm/opportunities/:id/",
    alias: "crm_opportunities_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedOpportunityRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Opportunity,
  },
  {
    method: "delete",
    path: "/api/crm/opportunities/:id/",
    alias: "crm_opportunities_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/opportunities/filter_options/",
    alias: "crm_opportunities_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Opportunity,
  },
  {
    method: "get",
    path: "/api/crm/subscriptions/",
    alias: "crm_subscriptions_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "end_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "start_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "subscription_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedSubscriptionList,
  },
  {
    method: "post",
    path: "/api/crm/subscriptions/",
    alias: "crm_subscriptions_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SubscriptionRequest,
      },
    ],
    response: Subscription,
  },
  {
    method: "get",
    path: "/api/crm/subscriptions/:id/",
    alias: "crm_subscriptions_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Subscription,
  },
  {
    method: "put",
    path: "/api/crm/subscriptions/:id/",
    alias: "crm_subscriptions_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SubscriptionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Subscription,
  },
  {
    method: "patch",
    path: "/api/crm/subscriptions/:id/",
    alias: "crm_subscriptions_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedSubscriptionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Subscription,
  },
  {
    method: "delete",
    path: "/api/crm/subscriptions/:id/",
    alias: "crm_subscriptions_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/subscriptions/filter_options/",
    alias: "crm_subscriptions_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Subscription,
  },
  {
    method: "get",
    path: "/api/crm/tasks/",
    alias: "crm_tasks_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "completed",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "due_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "opportunity",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "priority",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedTaskList,
  },
  {
    method: "post",
    path: "/api/crm/tasks/",
    alias: "crm_tasks_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaskRequest,
      },
    ],
    response: Task,
  },
  {
    method: "get",
    path: "/api/crm/tasks/:id/",
    alias: "crm_tasks_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "put",
    path: "/api/crm/tasks/:id/",
    alias: "crm_tasks_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaskRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "patch",
    path: "/api/crm/tasks/:id/",
    alias: "crm_tasks_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedTaskRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "delete",
    path: "/api/crm/tasks/:id/",
    alias: "crm_tasks_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/crm/tasks/filter_options/",
    alias: "crm_tasks_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Task,
  },
  {
    method: "get",
    path: "/api/hrm/attendances/",
    alias: "hrm_attendances_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "check_in",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "check_out",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "hours_worked",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedAttendanceList,
  },
  {
    method: "post",
    path: "/api/hrm/attendances/",
    alias: "hrm_attendances_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttendanceRequest,
      },
    ],
    response: Attendance,
  },
  {
    method: "get",
    path: "/api/hrm/attendances/:id/",
    alias: "hrm_attendances_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attendance,
  },
  {
    method: "put",
    path: "/api/hrm/attendances/:id/",
    alias: "hrm_attendances_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttendanceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attendance,
  },
  {
    method: "patch",
    path: "/api/hrm/attendances/:id/",
    alias: "hrm_attendances_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedAttendanceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attendance,
  },
  {
    method: "delete",
    path: "/api/hrm/attendances/:id/",
    alias: "hrm_attendances_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/attendances/filter_options/",
    alias: "hrm_attendances_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Attendance,
  },
  {
    method: "get",
    path: "/api/hrm/departments/",
    alias: "hrm_departments_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "location",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedDepartmentList,
  },
  {
    method: "post",
    path: "/api/hrm/departments/",
    alias: "hrm_departments_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: DepartmentRequest,
      },
    ],
    response: Department,
  },
  {
    method: "get",
    path: "/api/hrm/departments/:id/",
    alias: "hrm_departments_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Department,
  },
  {
    method: "put",
    path: "/api/hrm/departments/:id/",
    alias: "hrm_departments_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: DepartmentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Department,
  },
  {
    method: "patch",
    path: "/api/hrm/departments/:id/",
    alias: "hrm_departments_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedDepartmentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Department,
  },
  {
    method: "delete",
    path: "/api/hrm/departments/:id/",
    alias: "hrm_departments_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/departments/filter_options/",
    alias: "hrm_departments_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Department,
  },
  {
    method: "get",
    path: "/api/hrm/employee-form-options/",
    alias: "hrm_employee_form_options_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/employees/",
    alias: "hrm_employees_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "department",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "hire_date_after",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "hire_date_before",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "position",
        type: "Query",
        schema: z
          .array(
            z.enum([
              "accountant",
              "admin",
              "customer_service",
              "delivery",
              "employee",
              "hr",
              "manager",
              "marketing",
              "sales",
            ])
          )
          .optional(),
      },
      {
        name: "salary_max",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "salary_min",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "user__username",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedEmployeeList,
  },
  {
    method: "post",
    path: "/api/hrm/employees/",
    alias: "hrm_employees_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: EmployeeRequest,
      },
    ],
    response: Employee,
  },
  {
    method: "get",
    path: "/api/hrm/employees/:id/",
    alias: "hrm_employees_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Employee,
  },
  {
    method: "put",
    path: "/api/hrm/employees/:id/",
    alias: "hrm_employees_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: EmployeeRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Employee,
  },
  {
    method: "patch",
    path: "/api/hrm/employees/:id/",
    alias: "hrm_employees_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedEmployeeRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Employee,
  },
  {
    method: "delete",
    path: "/api/hrm/employees/:id/",
    alias: "hrm_employees_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/employees/filter_options/",
    alias: "hrm_employees_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Employee,
  },
  {
    method: "get",
    path: "/api/hrm/leaves/",
    alias: "hrm_leaves_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "end_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "leave_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "start_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedLeaveList,
  },
  {
    method: "post",
    path: "/api/hrm/leaves/",
    alias: "hrm_leaves_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LeaveRequest,
      },
    ],
    response: Leave,
  },
  {
    method: "get",
    path: "/api/hrm/leaves/:id/",
    alias: "hrm_leaves_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Leave,
  },
  {
    method: "put",
    path: "/api/hrm/leaves/:id/",
    alias: "hrm_leaves_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LeaveRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Leave,
  },
  {
    method: "patch",
    path: "/api/hrm/leaves/:id/",
    alias: "hrm_leaves_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedLeaveRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Leave,
  },
  {
    method: "delete",
    path: "/api/hrm/leaves/:id/",
    alias: "hrm_leaves_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/leaves/filter_options/",
    alias: "hrm_leaves_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Leave,
  },
  {
    method: "get",
    path: "/api/hrm/notifications/",
    alias: "hrm_notifications_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_read",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "message",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "notification_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedNotificationList,
  },
  {
    method: "post",
    path: "/api/hrm/notifications/",
    alias: "hrm_notifications_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: NotificationRequest,
      },
    ],
    response: Notification,
  },
  {
    method: "get",
    path: "/api/hrm/notifications/:id/",
    alias: "hrm_notifications_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Notification,
  },
  {
    method: "put",
    path: "/api/hrm/notifications/:id/",
    alias: "hrm_notifications_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: NotificationRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Notification,
  },
  {
    method: "patch",
    path: "/api/hrm/notifications/:id/",
    alias: "hrm_notifications_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedNotificationRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Notification,
  },
  {
    method: "delete",
    path: "/api/hrm/notifications/:id/",
    alias: "hrm_notifications_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/notifications/filter_options/",
    alias: "hrm_notifications_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Notification,
  },
  {
    method: "get",
    path: "/api/hrm/payrolls/",
    alias: "hrm_payrolls_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "basic_salary",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "bonuses",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "deductions",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "month",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "net_salary",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPayrollList,
  },
  {
    method: "post",
    path: "/api/hrm/payrolls/",
    alias: "hrm_payrolls_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PayrollRequest,
      },
    ],
    response: Payroll,
  },
  {
    method: "get",
    path: "/api/hrm/payrolls/:id/",
    alias: "hrm_payrolls_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payroll,
  },
  {
    method: "put",
    path: "/api/hrm/payrolls/:id/",
    alias: "hrm_payrolls_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PayrollRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payroll,
  },
  {
    method: "patch",
    path: "/api/hrm/payrolls/:id/",
    alias: "hrm_payrolls_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPayrollRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payroll,
  },
  {
    method: "delete",
    path: "/api/hrm/payrolls/:id/",
    alias: "hrm_payrolls_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/payrolls/filter_options/",
    alias: "hrm_payrolls_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Payroll,
  },
  {
    method: "get",
    path: "/api/hrm/performance-reviews/",
    alias: "hrm_performance_reviews_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "comments",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "rating",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "review_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPerformanceReviewList,
  },
  {
    method: "post",
    path: "/api/hrm/performance-reviews/",
    alias: "hrm_performance_reviews_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PerformanceReviewRequest,
      },
    ],
    response: PerformanceReview,
  },
  {
    method: "get",
    path: "/api/hrm/performance-reviews/:id/",
    alias: "hrm_performance_reviews_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PerformanceReview,
  },
  {
    method: "put",
    path: "/api/hrm/performance-reviews/:id/",
    alias: "hrm_performance_reviews_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PerformanceReviewRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PerformanceReview,
  },
  {
    method: "patch",
    path: "/api/hrm/performance-reviews/:id/",
    alias: "hrm_performance_reviews_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPerformanceReviewRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PerformanceReview,
  },
  {
    method: "delete",
    path: "/api/hrm/performance-reviews/:id/",
    alias: "hrm_performance_reviews_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/performance-reviews/filter_options/",
    alias: "hrm_performance_reviews_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: PerformanceReview,
  },
  {
    method: "get",
    path: "/api/hrm/tasks/",
    alias: "hrm_tasks_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "due_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "employee",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "title",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedTaskList,
  },
  {
    method: "post",
    path: "/api/hrm/tasks/",
    alias: "hrm_tasks_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaskRequest,
      },
    ],
    response: Task,
  },
  {
    method: "get",
    path: "/api/hrm/tasks/:id/",
    alias: "hrm_tasks_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "put",
    path: "/api/hrm/tasks/:id/",
    alias: "hrm_tasks_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TaskRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "patch",
    path: "/api/hrm/tasks/:id/",
    alias: "hrm_tasks_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedTaskRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Task,
  },
  {
    method: "delete",
    path: "/api/hrm/tasks/:id/",
    alias: "hrm_tasks_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/hrm/tasks/filter_options/",
    alias: "hrm_tasks_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Task,
  },
  {
    method: "get",
    path: "/api/prescriptions/prescription/",
    alias: "prescriptions_prescription_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_by__first_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_by__username",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer__email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer__first_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer__id",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "customer__last_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer__phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPrescriptionRecordList,
  },
  {
    method: "post",
    path: "/api/prescriptions/prescription/",
    alias: "prescriptions_prescription_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PrescriptionRecordRequest,
      },
    ],
    response: PrescriptionRecord,
  },
  {
    method: "get",
    path: "/api/prescriptions/prescription/:id/",
    alias: "prescriptions_prescription_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PrescriptionRecord,
  },
  {
    method: "put",
    path: "/api/prescriptions/prescription/:id/",
    alias: "prescriptions_prescription_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PrescriptionRecordRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PrescriptionRecord,
  },
  {
    method: "patch",
    path: "/api/prescriptions/prescription/:id/",
    alias: "prescriptions_prescription_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPrescriptionRecordRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: PrescriptionRecord,
  },
  {
    method: "delete",
    path: "/api/prescriptions/prescription/:id/",
    alias: "prescriptions_prescription_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/prescriptions/prescription/filter_options/",
    alias: "prescriptions_prescription_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: PrescriptionRecord,
  },
  {
    method: "get",
    path: "/api/products/answers/",
    alias: "products_answers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "answer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "answered_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "question_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantAnswerList,
  },
  {
    method: "post",
    path: "/api/products/answers/",
    alias: "products_answers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantAnswerRequest,
      },
    ],
    response: ProductVariantAnswer,
  },
  {
    method: "get",
    path: "/api/products/answers/:id/",
    alias: "products_answers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantAnswer,
  },
  {
    method: "put",
    path: "/api/products/answers/:id/",
    alias: "products_answers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantAnswerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantAnswer,
  },
  {
    method: "patch",
    path: "/api/products/answers/:id/",
    alias: "products_answers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantAnswerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantAnswer,
  },
  {
    method: "delete",
    path: "/api/products/answers/:id/",
    alias: "products_answers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/answers/filter_options/",
    alias: "products_answers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariantAnswer,
  },
  {
    method: "get",
    path: "/api/products/attribute-values/",
    alias: "products_attribute_values_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "attribute_id__name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "value",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "value__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedAttributeValueList,
  },
  {
    method: "post",
    path: "/api/products/attribute-values/",
    alias: "products_attribute_values_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttributeValueRequest,
      },
    ],
    response: AttributeValue,
  },
  {
    method: "get",
    path: "/api/products/attribute-values/:id/",
    alias: "products_attribute_values_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AttributeValue,
  },
  {
    method: "put",
    path: "/api/products/attribute-values/:id/",
    alias: "products_attribute_values_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttributeValueRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AttributeValue,
  },
  {
    method: "patch",
    path: "/api/products/attribute-values/:id/",
    alias: "products_attribute_values_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedAttributeValueRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: AttributeValue,
  },
  {
    method: "delete",
    path: "/api/products/attribute-values/:id/",
    alias: "products_attribute_values_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/attribute-values/filter_options/",
    alias: "products_attribute_values_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: AttributeValue,
  },
  {
    method: "get",
    path: "/api/products/attributes/",
    alias: "products_attributes_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "values",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedAttributesList,
  },
  {
    method: "post",
    path: "/api/products/attributes/",
    alias: "products_attributes_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttributesRequest,
      },
    ],
    response: Attributes,
  },
  {
    method: "get",
    path: "/api/products/attributes/:id/",
    alias: "products_attributes_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attributes,
  },
  {
    method: "put",
    path: "/api/products/attributes/:id/",
    alias: "products_attributes_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: AttributesRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attributes,
  },
  {
    method: "patch",
    path: "/api/products/attributes/:id/",
    alias: "products_attributes_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedAttributesRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Attributes,
  },
  {
    method: "delete",
    path: "/api/products/attributes/:id/",
    alias: "products_attributes_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/attributes/filter_options/",
    alias: "products_attributes_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Attributes,
  },
  {
    method: "get",
    path: "/api/products/brands/",
    alias: "products_brands_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "country",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "logo",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "product_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "website",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedBrandList,
  },
  {
    method: "post",
    path: "/api/products/brands/",
    alias: "products_brands_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BrandRequest,
      },
    ],
    response: Brand,
  },
  {
    method: "get",
    path: "/api/products/brands/:id/",
    alias: "products_brands_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Brand,
  },
  {
    method: "put",
    path: "/api/products/brands/:id/",
    alias: "products_brands_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: BrandRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Brand,
  },
  {
    method: "patch",
    path: "/api/products/brands/:id/",
    alias: "products_brands_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedBrandRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Brand,
  },
  {
    method: "delete",
    path: "/api/products/brands/:id/",
    alias: "products_brands_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/brands/filter_options/",
    alias: "products_brands_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Brand,
  },
  {
    method: "get",
    path: "/api/products/categories/",
    alias: "products_categories_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "parent_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "parent_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedCategoryList,
  },
  {
    method: "post",
    path: "/api/products/categories/",
    alias: "products_categories_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CategoryRequest,
      },
    ],
    response: Category,
  },
  {
    method: "get",
    path: "/api/products/categories/:id/",
    alias: "products_categories_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Category,
  },
  {
    method: "put",
    path: "/api/products/categories/:id/",
    alias: "products_categories_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: CategoryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Category,
  },
  {
    method: "patch",
    path: "/api/products/categories/:id/",
    alias: "products_categories_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedCategoryRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Category,
  },
  {
    method: "delete",
    path: "/api/products/categories/:id/",
    alias: "products_categories_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/categories/filter_options/",
    alias: "products_categories_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Category,
  },
  {
    method: "get",
    path: "/api/products/flexible-prices/",
    alias: "products_flexible_prices_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "branch",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "branch_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "currency",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer_group",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer_group_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "end_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "min_quantity",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "priority",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "special_price",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "start_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedFlexiblePriceList,
  },
  {
    method: "post",
    path: "/api/products/flexible-prices/",
    alias: "products_flexible_prices_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: FlexiblePriceRequest,
      },
    ],
    response: FlexiblePrice,
  },
  {
    method: "get",
    path: "/api/products/flexible-prices/:id/",
    alias: "products_flexible_prices_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FlexiblePrice,
  },
  {
    method: "put",
    path: "/api/products/flexible-prices/:id/",
    alias: "products_flexible_prices_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: FlexiblePriceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FlexiblePrice,
  },
  {
    method: "patch",
    path: "/api/products/flexible-prices/:id/",
    alias: "products_flexible_prices_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedFlexiblePriceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: FlexiblePrice,
  },
  {
    method: "delete",
    path: "/api/products/flexible-prices/:id/",
    alias: "products_flexible_prices_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/flexible-prices/filter_options/",
    alias: "products_flexible_prices_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: FlexiblePrice,
  },
  {
    method: "get",
    path: "/api/products/manufacturers/",
    alias: "products_manufacturers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "country",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "website",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedManufacturerList,
  },
  {
    method: "post",
    path: "/api/products/manufacturers/",
    alias: "products_manufacturers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ManufacturerRequest,
      },
    ],
    response: Manufacturer,
  },
  {
    method: "get",
    path: "/api/products/manufacturers/:id/",
    alias: "products_manufacturers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Manufacturer,
  },
  {
    method: "put",
    path: "/api/products/manufacturers/:id/",
    alias: "products_manufacturers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ManufacturerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Manufacturer,
  },
  {
    method: "patch",
    path: "/api/products/manufacturers/:id/",
    alias: "products_manufacturers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedManufacturerRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Manufacturer,
  },
  {
    method: "delete",
    path: "/api/products/manufacturers/:id/",
    alias: "products_manufacturers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/manufacturers/filter_options/",
    alias: "products_manufacturers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Manufacturer,
  },
  {
    method: "get",
    path: "/api/products/marketing/",
    alias: "products_marketing_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "age_group",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "gender",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "meta_description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "meta_keywords",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "meta_title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "seo_image",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "seo_image_alt",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "slug",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant_id",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantMarketingList,
  },
  {
    method: "post",
    path: "/api/products/marketing/",
    alias: "products_marketing_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantMarketingRequest,
      },
    ],
    response: ProductVariantMarketing,
  },
  {
    method: "get",
    path: "/api/products/marketing/:id/",
    alias: "products_marketing_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantMarketing,
  },
  {
    method: "put",
    path: "/api/products/marketing/:id/",
    alias: "products_marketing_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantMarketingRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantMarketing,
  },
  {
    method: "patch",
    path: "/api/products/marketing/:id/",
    alias: "products_marketing_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantMarketingRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantMarketing,
  },
  {
    method: "delete",
    path: "/api/products/marketing/:id/",
    alias: "products_marketing_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/marketing/filter_options/",
    alias: "products_marketing_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariantMarketing,
  },
  {
    method: "get",
    path: "/api/products/offers/",
    alias: "products_offers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "ProductVariant_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "end_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "offer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "start_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantOfferList,
  },
  {
    method: "post",
    path: "/api/products/offers/",
    alias: "products_offers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantOfferRequest,
      },
    ],
    response: ProductVariantOffer,
  },
  {
    method: "get",
    path: "/api/products/offers/:id/",
    alias: "products_offers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantOffer,
  },
  {
    method: "put",
    path: "/api/products/offers/:id/",
    alias: "products_offers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantOfferRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantOffer,
  },
  {
    method: "patch",
    path: "/api/products/offers/:id/",
    alias: "products_offers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantOfferRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantOffer,
  },
  {
    method: "delete",
    path: "/api/products/offers/:id/",
    alias: "products_offers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/offers/filter_options/",
    alias: "products_offers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariantOffer,
  },
  {
    method: "get",
    path: "/api/products/product-images/",
    alias: "products_product_images_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "alt_text",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "image",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_primary",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "order",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant_id",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductImageList,
  },
  {
    method: "post",
    path: "/api/products/product-images/",
    alias: "products_product_images_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductImageRequest,
      },
    ],
    response: ProductImage,
  },
  {
    method: "get",
    path: "/api/products/product-images/:id/",
    alias: "products_product_images_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductImage,
  },
  {
    method: "put",
    path: "/api/products/product-images/:id/",
    alias: "products_product_images_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductImageRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductImage,
  },
  {
    method: "patch",
    path: "/api/products/product-images/:id/",
    alias: "products_product_images_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductImageRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductImage,
  },
  {
    method: "delete",
    path: "/api/products/product-images/:id/",
    alias: "products_product_images_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/product-images/filter_options/",
    alias: "products_product_images_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductImage,
  },
  {
    method: "get",
    path: "/api/products/products/",
    alias: "products_products_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "brand",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "brand_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "category",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "category_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "manufacturer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "manufacturer_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "model",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "supplier",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "supplier_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "usku",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variants",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductList,
  },
  {
    method: "post",
    path: "/api/products/products/",
    alias: "products_products_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductRequest,
      },
    ],
    response: Product,
  },
  {
    method: "get",
    path: "/api/products/products/:id/",
    alias: "products_products_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Product,
  },
  {
    method: "put",
    path: "/api/products/products/:id/",
    alias: "products_products_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Product,
  },
  {
    method: "patch",
    path: "/api/products/products/:id/",
    alias: "products_products_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Product,
  },
  {
    method: "delete",
    path: "/api/products/products/:id/",
    alias: "products_products_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/products/filter_options/",
    alias: "products_products_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Product,
  },
  {
    method: "get",
    path: "/api/products/questions/",
    alias: "products_questions_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "ProductVariant_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "asked_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "question",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantQuestionList,
  },
  {
    method: "post",
    path: "/api/products/questions/",
    alias: "products_questions_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantQuestionRequest,
      },
    ],
    response: ProductVariantQuestion,
  },
  {
    method: "get",
    path: "/api/products/questions/:id/",
    alias: "products_questions_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantQuestion,
  },
  {
    method: "put",
    path: "/api/products/questions/:id/",
    alias: "products_questions_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantQuestionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantQuestion,
  },
  {
    method: "patch",
    path: "/api/products/questions/:id/",
    alias: "products_questions_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantQuestionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantQuestion,
  },
  {
    method: "delete",
    path: "/api/products/questions/:id/",
    alias: "products_questions_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/questions/filter_options/",
    alias: "products_questions_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariantQuestion,
  },
  {
    method: "get",
    path: "/api/products/reviews/",
    alias: "products_reviews_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "ProductVariant_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "rating",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "review",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "reviewed_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantReviewList,
  },
  {
    method: "post",
    path: "/api/products/reviews/",
    alias: "products_reviews_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantReviewRequest,
      },
    ],
    response: ProductVariantReview,
  },
  {
    method: "get",
    path: "/api/products/reviews/:id/",
    alias: "products_reviews_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantReview,
  },
  {
    method: "put",
    path: "/api/products/reviews/:id/",
    alias: "products_reviews_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantReviewRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantReview,
  },
  {
    method: "patch",
    path: "/api/products/reviews/:id/",
    alias: "products_reviews_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantReviewRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariantReview,
  },
  {
    method: "delete",
    path: "/api/products/reviews/:id/",
    alias: "products_reviews_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/reviews/filter_options/",
    alias: "products_reviews_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariantReview,
  },
  {
    method: "get",
    path: "/api/products/stock-movements/",
    alias: "products_stock_movements_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "cost_per_unit",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "movement_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "movement_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "quantity",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "quantity_after",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "quantity_before",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "reference_number",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "stocks_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedStockMovementsList,
  },
  {
    method: "post",
    path: "/api/products/stock-movements/",
    alias: "products_stock_movements_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockMovementsRequest,
      },
    ],
    response: StockMovements,
  },
  {
    method: "get",
    path: "/api/products/stock-movements/:id/",
    alias: "products_stock_movements_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockMovements,
  },
  {
    method: "put",
    path: "/api/products/stock-movements/:id/",
    alias: "products_stock_movements_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockMovementsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockMovements,
  },
  {
    method: "patch",
    path: "/api/products/stock-movements/:id/",
    alias: "products_stock_movements_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedStockMovementsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockMovements,
  },
  {
    method: "delete",
    path: "/api/products/stock-movements/:id/",
    alias: "products_stock_movements_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/stock-movements/filter_options/",
    alias: "products_stock_movements_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: StockMovements,
  },
  {
    method: "get",
    path: "/api/products/stock-transfer-items/",
    alias: "products_stock_transfer_items_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "quantity_received",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "quantity_requested",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "quantity_sent",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "transfer_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "unit_cost",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant_id",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedStockTransferItemList,
  },
  {
    method: "post",
    path: "/api/products/stock-transfer-items/",
    alias: "products_stock_transfer_items_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockTransferItemRequest,
      },
    ],
    response: StockTransferItem,
  },
  {
    method: "get",
    path: "/api/products/stock-transfer-items/:id/",
    alias: "products_stock_transfer_items_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransferItem,
  },
  {
    method: "put",
    path: "/api/products/stock-transfer-items/:id/",
    alias: "products_stock_transfer_items_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockTransferItemRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransferItem,
  },
  {
    method: "patch",
    path: "/api/products/stock-transfer-items/:id/",
    alias: "products_stock_transfer_items_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedStockTransferItemRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransferItem,
  },
  {
    method: "delete",
    path: "/api/products/stock-transfer-items/:id/",
    alias: "products_stock_transfer_items_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/stock-transfer-items/filter_options/",
    alias: "products_stock_transfer_items_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: StockTransferItem,
  },
  {
    method: "get",
    path: "/api/products/stock-transfers/",
    alias: "products_stock_transfers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "approved_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "approved_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "from_branch_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "received_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "requested_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "requested_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "shipped_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "to_branch_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "transfer_number",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedStockTransferList,
  },
  {
    method: "post",
    path: "/api/products/stock-transfers/",
    alias: "products_stock_transfers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockTransferRequest,
      },
    ],
    response: StockTransfer,
  },
  {
    method: "get",
    path: "/api/products/stock-transfers/:id/",
    alias: "products_stock_transfers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransfer,
  },
  {
    method: "put",
    path: "/api/products/stock-transfers/:id/",
    alias: "products_stock_transfers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StockTransferRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransfer,
  },
  {
    method: "patch",
    path: "/api/products/stock-transfers/:id/",
    alias: "products_stock_transfers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedStockTransferRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: StockTransfer,
  },
  {
    method: "delete",
    path: "/api/products/stock-transfers/:id/",
    alias: "products_stock_transfers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/stock-transfers/filter_options/",
    alias: "products_stock_transfers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: StockTransfer,
  },
  {
    method: "get",
    path: "/api/products/stocks/",
    alias: "products_stocks_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "allow_backorder",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "average_cost",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "branch_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "last_restocked",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "last_sale",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "max_stock_level",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "min_stock_level",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "quantity_in_stock",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "reorder_level",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "reserved_quantity",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "variant_id",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedStocksList,
  },
  {
    method: "post",
    path: "/api/products/stocks/",
    alias: "products_stocks_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StocksRequest,
      },
    ],
    response: Stocks,
  },
  {
    method: "get",
    path: "/api/products/stocks/:id/",
    alias: "products_stocks_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Stocks,
  },
  {
    method: "put",
    path: "/api/products/stocks/:id/",
    alias: "products_stocks_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: StocksRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Stocks,
  },
  {
    method: "patch",
    path: "/api/products/stocks/:id/",
    alias: "products_stocks_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedStocksRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Stocks,
  },
  {
    method: "delete",
    path: "/api/products/stocks/:id/",
    alias: "products_stocks_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/stocks/filter_options/",
    alias: "products_stocks_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Stocks,
  },
  {
    method: "get",
    path: "/api/products/suppliers/",
    alias: "products_suppliers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "address",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "contact_person",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "country",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "payment_terms",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "website",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedSupplierList,
  },
  {
    method: "post",
    path: "/api/products/suppliers/",
    alias: "products_suppliers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SupplierRequest,
      },
    ],
    response: Supplier,
  },
  {
    method: "get",
    path: "/api/products/suppliers/:id/",
    alias: "products_suppliers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Supplier,
  },
  {
    method: "put",
    path: "/api/products/suppliers/:id/",
    alias: "products_suppliers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SupplierRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Supplier,
  },
  {
    method: "patch",
    path: "/api/products/suppliers/:id/",
    alias: "products_suppliers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedSupplierRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Supplier,
  },
  {
    method: "delete",
    path: "/api/products/suppliers/:id/",
    alias: "products_suppliers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/suppliers/filter_options/",
    alias: "products_suppliers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Supplier,
  },
  {
    method: "get",
    path: "/api/products/variants/",
    alias: "products_variants_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "dimensions",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "discount_percentage",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "last_purchase_price",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "product",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "product_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "product_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "selling_price",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "sku",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "usku",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "warranty",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "weight",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedProductVariantList,
  },
  {
    method: "post",
    path: "/api/products/variants/",
    alias: "products_variants_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantRequest,
      },
    ],
    response: ProductVariant,
  },
  {
    method: "get",
    path: "/api/products/variants/:id/",
    alias: "products_variants_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariant,
  },
  {
    method: "put",
    path: "/api/products/variants/:id/",
    alias: "products_variants_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ProductVariantRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariant,
  },
  {
    method: "patch",
    path: "/api/products/variants/:id/",
    alias: "products_variants_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedProductVariantRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ProductVariant,
  },
  {
    method: "delete",
    path: "/api/products/variants/:id/",
    alias: "products_variants_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/products/variants/filter_options/",
    alias: "products_variants_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ProductVariant,
  },
  {
    method: "get",
    path: "/api/sales/invoices/",
    alias: "sales_invoices_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "branch",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_by",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "discount_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "due_date",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "invoice_number",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "invoice_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "items",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "order",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "paid_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "subtotal",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "tax_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "tax_rate",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "total_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedInvoiceList,
  },
  {
    method: "post",
    path: "/api/sales/invoices/",
    alias: "sales_invoices_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InvoiceRequest,
      },
    ],
    response: Invoice,
  },
  {
    method: "get",
    path: "/api/sales/invoices/:id/",
    alias: "sales_invoices_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Invoice,
  },
  {
    method: "put",
    path: "/api/sales/invoices/:id/",
    alias: "sales_invoices_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InvoiceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Invoice,
  },
  {
    method: "patch",
    path: "/api/sales/invoices/:id/",
    alias: "sales_invoices_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedInvoiceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Invoice,
  },
  {
    method: "delete",
    path: "/api/sales/invoices/:id/",
    alias: "sales_invoices_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/sales/invoices/:id/calculate_totals/",
    alias: "sales_invoices_calculate_totals_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InvoiceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Invoice,
  },
  {
    method: "post",
    path: "/api/sales/invoices/:id/confirm/",
    alias: "sales_invoices_confirm_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: InvoiceRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Invoice,
  },
  {
    method: "get",
    path: "/api/sales/invoices/choices/",
    alias: "sales_invoices_choices_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/sales/invoices/filter_options/",
    alias: "sales_invoices_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Invoice,
  },
  {
    method: "get",
    path: "/api/sales/orders/",
    alias: "sales_orders_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "branch",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "confirmed_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "customer",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "delivered_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "discount_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "expected_delivery",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "internal_notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "items",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "notes",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "order_number",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "order_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "paid_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "payment_status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "payment_type",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "sales_person",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "status",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "subtotal",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "tax_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "tax_rate",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "total_amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedOrderList,
  },
  {
    method: "post",
    path: "/api/sales/orders/",
    alias: "sales_orders_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrderRequest,
      },
    ],
    response: Order,
  },
  {
    method: "get",
    path: "/api/sales/orders/:id/",
    alias: "sales_orders_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "put",
    path: "/api/sales/orders/:id/",
    alias: "sales_orders_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrderRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "patch",
    path: "/api/sales/orders/:id/",
    alias: "sales_orders_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedOrderRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "delete",
    path: "/api/sales/orders/:id/",
    alias: "sales_orders_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/sales/orders/:id/calculate_totals/",
    alias: "sales_orders_calculate_totals_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrderRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "post",
    path: "/api/sales/orders/:id/cancel/",
    alias: "sales_orders_cancel_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrderRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "post",
    path: "/api/sales/orders/:id/confirm/",
    alias: "sales_orders_confirm_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrderRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Order,
  },
  {
    method: "get",
    path: "/api/sales/orders/choices/",
    alias: "sales_orders_choices_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/sales/orders/filter_options/",
    alias: "sales_orders_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Order,
  },
  {
    method: "get",
    path: "/api/sales/payments/",
    alias: "sales_payments_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "amount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "invoice",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "payment_method",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPaymentList,
  },
  {
    method: "post",
    path: "/api/sales/payments/",
    alias: "sales_payments_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PaymentRequest,
      },
    ],
    response: Payment,
  },
  {
    method: "get",
    path: "/api/sales/payments/:id/",
    alias: "sales_payments_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payment,
  },
  {
    method: "put",
    path: "/api/sales/payments/:id/",
    alias: "sales_payments_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PaymentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payment,
  },
  {
    method: "patch",
    path: "/api/sales/payments/:id/",
    alias: "sales_payments_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPaymentRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Payment,
  },
  {
    method: "delete",
    path: "/api/sales/payments/:id/",
    alias: "sales_payments_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/sales/payments/filter_options/",
    alias: "sales_payments_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Payment,
  },
  {
    method: "get",
    path: "/api/tenants/activate/",
    alias: "tenants_activate_retrieve",
    description: `Main algorithm execution with improved flow control`,
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/clients/",
    alias: "tenants_clients_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedClientList,
  },
  {
    method: "post",
    path: "/api/tenants/clients/",
    alias: "tenants_clients_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ClientRequest,
      },
    ],
    response: Client,
  },
  {
    method: "get",
    path: "/api/tenants/clients/:id/",
    alias: "tenants_clients_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: Client,
  },
  {
    method: "put",
    path: "/api/tenants/clients/:id/",
    alias: "tenants_clients_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ClientRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: Client,
  },
  {
    method: "patch",
    path: "/api/tenants/clients/:id/",
    alias: "tenants_clients_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedClientRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: Client,
  },
  {
    method: "delete",
    path: "/api/tenants/clients/:id/",
    alias: "tenants_clients_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/clients/filter_options/",
    alias: "tenants_clients_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Client,
  },
  {
    method: "post",
    path: "/api/tenants/create-payment-order/",
    alias: "tenants_create_payment_order_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/domain/",
    alias: "tenants_domain_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/payments/",
    alias: "tenants_payments_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/paypal/cancel/",
    alias: "tenants_paypal_cancel_retrieve",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/tenants/paypal/execute/",
    alias: "tenants_paypal_execute_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/tenants/paypal/webhook/",
    alias: "tenants_paypal_webhook_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/tenants/register/",
    alias: "tenants_register_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/registers/",
    alias: "tenants_registers_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "password",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedRegisterTenantList,
  },
  {
    method: "post",
    path: "/api/tenants/registers/",
    alias: "tenants_registers_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RegisterTenantRequest,
      },
    ],
    response: RegisterTenant,
  },
  {
    method: "get",
    path: "/api/tenants/registers/:id/",
    alias: "tenants_registers_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RegisterTenant,
  },
  {
    method: "put",
    path: "/api/tenants/registers/:id/",
    alias: "tenants_registers_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RegisterTenantRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RegisterTenant,
  },
  {
    method: "patch",
    path: "/api/tenants/registers/:id/",
    alias: "tenants_registers_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedRegisterTenantRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RegisterTenant,
  },
  {
    method: "delete",
    path: "/api/tenants/registers/:id/",
    alias: "tenants_registers_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/registers/filter_options/",
    alias: "tenants_registers_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: RegisterTenant,
  },
  {
    method: "get",
    path: "/api/tenants/subscription-plans/",
    alias: "tenants_subscription_plans_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "currency",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "discount",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "duration_months",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "duration_years",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "field_labels",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "max_branches",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "max_products",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "max_users",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "month_price",
        type: "Query",
        schema: z.number().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "year_price",
        type: "Query",
        schema: z.number().optional(),
      },
    ],
    response: PaginatedSubscriptionPlanList,
  },
  {
    method: "post",
    path: "/api/tenants/subscription-plans/",
    alias: "tenants_subscription_plans_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SubscriptionPlanRequest,
      },
    ],
    response: SubscriptionPlan,
  },
  {
    method: "get",
    path: "/api/tenants/subscription-plans/:id/",
    alias: "tenants_subscription_plans_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: SubscriptionPlan,
  },
  {
    method: "put",
    path: "/api/tenants/subscription-plans/:id/",
    alias: "tenants_subscription_plans_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SubscriptionPlanRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: SubscriptionPlan,
  },
  {
    method: "patch",
    path: "/api/tenants/subscription-plans/:id/",
    alias: "tenants_subscription_plans_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedSubscriptionPlanRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: SubscriptionPlan,
  },
  {
    method: "delete",
    path: "/api/tenants/subscription-plans/:id/",
    alias: "tenants_subscription_plans_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/tenants/subscription-plans/filter_options/",
    alias: "tenants_subscription_plans_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: SubscriptionPlan,
  },
  {
    method: "get",
    path: "/api/users/contact-us/",
    alias: "users_contact_us_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "message",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedContactUsList,
  },
  {
    method: "post",
    path: "/api/users/contact-us/",
    alias: "users_contact_us_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ContactUsRequest,
      },
    ],
    response: ContactUs,
  },
  {
    method: "get",
    path: "/api/users/contact-us/:id/",
    alias: "users_contact_us_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ContactUs,
  },
  {
    method: "put",
    path: "/api/users/contact-us/:id/",
    alias: "users_contact_us_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ContactUsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ContactUs,
  },
  {
    method: "patch",
    path: "/api/users/contact-us/:id/",
    alias: "users_contact_us_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedContactUsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: ContactUs,
  },
  {
    method: "delete",
    path: "/api/users/contact-us/:id/",
    alias: "users_contact_us_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/contact-us/filter_options/",
    alias: "users_contact_us_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: ContactUs,
  },
  {
    method: "post",
    path: "/api/users/login/",
    alias: "users_login_create",
    description: `Login endpoint for users`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LoginRequest,
      },
    ],
    response: z.object({ msg: z.string() }).passthrough(),
    errors: [
      {
        status: 400,
        schema: LoginBadRequest,
      },
      {
        status: 403,
        schema: z.object({ detail: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "post",
    path: "/api/users/logout/",
    alias: "users_logout_create",
    description: `Logout endpoint for users`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: z.object({ msg: z.string() }).passthrough(),
    errors: [
      {
        status: 401,
        schema: z.object({ error: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/users/pages/",
    alias: "users_pages_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "author_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "default_language",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_published",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "slug",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "translations",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPageList,
  },
  {
    method: "post",
    path: "/api/users/pages/",
    alias: "users_pages_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PageRequest,
      },
    ],
    response: Page,
  },
  {
    method: "get",
    path: "/api/users/pages/:id/",
    alias: "users_pages_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Page,
  },
  {
    method: "put",
    path: "/api/users/pages/:id/",
    alias: "users_pages_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PageRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Page,
  },
  {
    method: "patch",
    path: "/api/users/pages/:id/",
    alias: "users_pages_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPageRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Page,
  },
  {
    method: "delete",
    path: "/api/users/pages/:id/",
    alias: "users_pages_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/pages/filter_options/",
    alias: "users_pages_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Page,
  },
  {
    method: "post",
    path: "/api/users/password-reset-confirm/",
    alias: "users_password_reset_confirm_create",
    requestFormat: "json",
    response: z.void(),
  },
  {
    method: "post",
    path: "/api/users/password-reset/",
    alias: "users_password_reset_create",
    description: `Request password reset`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({}).partial().passthrough(),
      },
    ],
    response: z.object({ detail: z.string() }).passthrough(),
    errors: [
      {
        status: 400,
        schema: PasswordResetBadRequest,
      },
    ],
  },
  {
    method: "get",
    path: "/api/users/permissions/",
    alias: "users_permissions_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "code",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedPermissionList,
  },
  {
    method: "post",
    path: "/api/users/permissions/",
    alias: "users_permissions_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PermissionRequest,
      },
    ],
    response: Permission,
  },
  {
    method: "get",
    path: "/api/users/permissions/:id/",
    alias: "users_permissions_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Permission,
  },
  {
    method: "put",
    path: "/api/users/permissions/:id/",
    alias: "users_permissions_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PermissionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Permission,
  },
  {
    method: "patch",
    path: "/api/users/permissions/:id/",
    alias: "users_permissions_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedPermissionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Permission,
  },
  {
    method: "delete",
    path: "/api/users/permissions/:id/",
    alias: "users_permissions_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/permissions/filter_options/",
    alias: "users_permissions_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Permission,
  },
  {
    method: "get",
    path: "/api/users/profile/",
    alias: "users_profile_retrieve",
    description: `Get current authenticated user profile data`,
    requestFormat: "json",
    response: User,
    errors: [
      {
        status: 401,
        schema: z.object({ error: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/users/public/pages/",
    alias: "users_public_pages_list",
    description: `For public pages only`,
    requestFormat: "json",
    parameters: [
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
    ],
    response: PaginatedPageList,
  },
  {
    method: "get",
    path: "/api/users/public/pages/:slug/",
    alias: "users_public_pages_retrieve",
    description: `For public pages only`,
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: Page,
  },
  {
    method: "post",
    path: "/api/users/register/",
    alias: "users_register_create",
    description: `Register endpoint for users`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RegisterRequest,
      },
    ],
    response: RegisterSuccessResponse,
  },
  {
    method: "get",
    path: "/api/users/role-permissions/",
    alias: "users_role_permissions_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "permission_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "permission_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "role_id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "role_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedRolePermissionList,
  },
  {
    method: "post",
    path: "/api/users/role-permissions/",
    alias: "users_role_permissions_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RolePermissionRequest,
      },
    ],
    response: RolePermission,
  },
  {
    method: "get",
    path: "/api/users/role-permissions/:id/",
    alias: "users_role_permissions_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RolePermission,
  },
  {
    method: "put",
    path: "/api/users/role-permissions/:id/",
    alias: "users_role_permissions_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: RolePermissionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RolePermission,
  },
  {
    method: "patch",
    path: "/api/users/role-permissions/:id/",
    alias: "users_role_permissions_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedRolePermissionRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: RolePermission,
  },
  {
    method: "delete",
    path: "/api/users/role-permissions/:id/",
    alias: "users_role_permissions_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/role-permissions/filter_options/",
    alias: "users_role_permissions_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: RolePermission,
  },
  {
    method: "get",
    path: "/api/users/roles/",
    alias: "users_roles_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "permissions",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedRoleList,
  },
  {
    method: "post",
    path: "/api/users/roles/",
    alias: "users_roles_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ name: z.string().min(1).max(50) }).passthrough(),
      },
    ],
    response: Role,
  },
  {
    method: "get",
    path: "/api/users/roles/:id/",
    alias: "users_roles_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Role,
  },
  {
    method: "put",
    path: "/api/users/roles/:id/",
    alias: "users_roles_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ name: z.string().min(1).max(50) }).passthrough(),
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Role,
  },
  {
    method: "patch",
    path: "/api/users/roles/:id/",
    alias: "users_roles_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z
          .object({ name: z.string().min(1).max(50) })
          .partial()
          .passthrough(),
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: Role,
  },
  {
    method: "delete",
    path: "/api/users/roles/:id/",
    alias: "users_roles_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/roles/filter_options/",
    alias: "users_roles_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: Role,
  },
  {
    method: "get",
    path: "/api/users/tenant-settings/",
    alias: "users_tenant_settings_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "account_number",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "address",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "bank_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "business_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "city",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "country",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "created_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "facebook",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "iban",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "id",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "instagram",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "is_active",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "is_deleted",
        type: "Query",
        schema: z.boolean().optional(),
      },
      {
        name: "linkedin",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "logo",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "postal_code",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "seo_description",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "seo_keywords",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "seo_title",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "state",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "swift_code",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "tiktok",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "twitter",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "updated_at",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "website",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "whatsapp",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedTenantSettingsList,
  },
  {
    method: "post",
    path: "/api/users/tenant-settings/",
    alias: "users_tenant_settings_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TenantSettingsRequest,
      },
    ],
    response: TenantSettings,
  },
  {
    method: "get",
    path: "/api/users/tenant-settings/:id/",
    alias: "users_tenant_settings_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: TenantSettings,
  },
  {
    method: "put",
    path: "/api/users/tenant-settings/:id/",
    alias: "users_tenant_settings_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: TenantSettingsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: TenantSettings,
  },
  {
    method: "patch",
    path: "/api/users/tenant-settings/:id/",
    alias: "users_tenant_settings_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedTenantSettingsRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: TenantSettings,
  },
  {
    method: "delete",
    path: "/api/users/tenant-settings/:id/",
    alias: "users_tenant_settings_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/tenant-settings/filter_options/",
    alias: "users_tenant_settings_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: TenantSettings,
  },
  {
    method: "post",
    path: "/api/users/token/refresh/",
    alias: "users_token_refresh_create",
    requestFormat: "json",
    response: RefreshTokenResponse,
    errors: [
      {
        status: 401,
        schema: z.object({ error: z.string() }).passthrough(),
      },
    ],
  },
  {
    method: "get",
    path: "/api/users/users/",
    alias: "users_users_list",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "email",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "email__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "first_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "first_name__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "last_name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "last_name__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "ordering",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "page",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "page_size",
        type: "Query",
        schema: z.number().int().optional(),
      },
      {
        name: "phone",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "phone__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "role_id__name",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "search",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "username",
        type: "Query",
        schema: z.string().optional(),
      },
      {
        name: "username__icontains",
        type: "Query",
        schema: z.string().optional(),
      },
    ],
    response: PaginatedUserList,
  },
  {
    method: "post",
    path: "/api/users/users/",
    alias: "users_users_create",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserRequest,
      },
    ],
    response: User,
  },
  {
    method: "get",
    path: "/api/users/users/:id/",
    alias: "users_users_retrieve",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: User,
  },
  {
    method: "put",
    path: "/api/users/users/:id/",
    alias: "users_users_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: User,
  },
  {
    method: "patch",
    path: "/api/users/users/:id/",
    alias: "users_users_partial_update",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PatchedUserRequest,
      },
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: User,
  },
  {
    method: "delete",
    path: "/api/users/users/:id/",
    alias: "users_users_destroy",
    description: `Mixin that dynamically generates filtering options for any ViewSet.`,
    requestFormat: "json",
    parameters: [
      {
        name: "id",
        type: "Path",
        schema: z.number().int(),
      },
    ],
    response: z.void(),
  },
  {
    method: "get",
    path: "/api/users/users/filter_options/",
    alias: "users_users_filter_options_retrieve",
    description: `API endpoint to fetch available filtering options (for frontend).`,
    requestFormat: "json",
    response: User,
  },
]);

export const api = new Zodios(endpoints);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}
