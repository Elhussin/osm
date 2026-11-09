// Select styles 
const customStyles = {
    control: (provided: any) => ({
      ...provided,
      width: '100%',
      padding: '0.25rem',
      borderRadius: '0.5rem',
      borderColor: 'var(--color-border-main)',
      backgroundColor: 'var(--color-surface)',
      color: 'var(--color-main)',
      boxShadow: 'none',
      '&:hover': {
        borderColor: 'var(--color-primary)',
      },
    }),
    option: (provided: any, state: any) => ({
      ...provided,
      cursor: 'pointer',
      backgroundColor: state.isSelected
        ? 'var(--color-primary)'
        : state.isFocused
        ? 'var(--color-elevated)'
        : 'var(--color-surface)',
      color: state.isSelected ? 'var(--color-button-text)' : 'var(--color-main)',
    }),
    menu: (provided: any) => ({
      ...provided,
      zIndex: 50,
      backgroundColor: 'var(--color-surface)',
    }),
    singleValue: (provided: any) => ({
      ...provided,
      color: 'var(--color-main)',
    }),
    placeholder: (provided: any) => ({
      ...provided,
      color: 'var(--color-secondary)',
    }),
  };

export default customStyles;
