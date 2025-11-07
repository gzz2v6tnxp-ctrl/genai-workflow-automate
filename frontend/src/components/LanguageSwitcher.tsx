import React from 'react'
import { t, Lang } from '../i18n/translations'

interface Props {
  lang: Lang
  onChange: (l: Lang) => void
}

export const LanguageSwitcher: React.FC<Props> = ({ lang, onChange }) => {
  return (
    <div className="lang-switch" aria-label={t(lang,'language')}>
      {(['fr','en'] as Lang[]).map(code => (
        <button
          key={code}
          className={code === lang ? 'active' : ''}
          onClick={() => onChange(code)}
        >{code.toUpperCase()}</button>
      ))}
    </div>
  )
}
