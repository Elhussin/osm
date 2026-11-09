'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import {Table} from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableHeader from '@tiptap/extension-table-header';
import TableCell from '@tiptap/extension-table-cell';
import TextAlign from '@tiptap/extension-text-align';
import Color from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import {TextStyle} from '@tiptap/extension-text-style';
import { useCallback } from 'react';
import { Language, LANGUAGES } from '@/src/features/pages/types';

interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  editable?: boolean;
  language: Language;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({
  content,
  onChange,
  placeholder = 'Start writing...',
  editable = true,
  language,
}) => {
  const currentLang = LANGUAGES[language];
  const isRTL = currentLang.dir === 'rtl';
  
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 underline',
        },
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full h-auto rounded-lg',
        },
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Color.configure({ types: [TextStyle.name] }),
      Highlight.configure({ multicolor: true }),
      TextStyle,
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        dir: currentLang.dir,
        class: `prose max-w-none focus:outline-none ${isRTL ? 'prose-rtl' : ''}`,
      },
    },
    immediatelyRender: false,
  });

  const addImage = useCallback(() => {
    const url = window.prompt('Enter image URL:');
    if (url && editor) {
      editor.chain().focus().setImage({ src: url }).run();
    }
  }, [editor]);

  const setLink = useCallback(() => {
    const previousUrl = editor?.getAttributes('link').href;
    const url = window.prompt('Enter URL:', previousUrl);

    if (url === null) {
      return;
    }

    if (url === '') {
      editor?.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }

    editor?.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  }, [editor]);

  if (!editor) {
    return null;
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      {/* Language indicator and direction info */}
      <div className="bg-blue-50 px-3 py-2 text-sm text-blue-700 border-b border-blue-200">
        {currentLang.flag} {currentLang.name} ({currentLang.dir.toUpperCase()})
      </div>
      
      {/* Toolbar */}
      <div className={`border-b border-gray-200 p-3 bg-surface flex flex-wrap gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
        {/* Text Formatting */}
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('bold')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Bold
        </button>
        
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('italic')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Italic
        </button>
        <button
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('underline')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Underline
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHighlight().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('highlight')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Highlight
        </button>

        <button
          onClick={() => editor.chain().focus().toggleStrike().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('strike')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Strike
        </button>

        {/* Headings */}
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('heading', { level: 1 })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          H1
        </button>

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('heading', { level: 2 })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          H2
        </button>

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('heading', { level: 3 })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          H3
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 4 }).run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('heading', { level: 4 })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          H4
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 5 }).run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('heading', { level: 5 })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          H5
        </button>
        {/* Lists */}
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('bulletList')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          • List
        </button>

        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('orderedList')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          1. List
        </button>

        {/* Quote */}
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('blockquote')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Quote
        </button>

        {/* Code */}
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('codeBlock')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Code
        </button>

        {/* Link */}
        <button
          onClick={setLink}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive('link')
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Link
        </button>

        {/* Image */}
        <button
          onClick={addImage}
          className="px-3 py-1 text-sm font-medium rounded bg-white text-gray-700 hover:bg-gray-100"
        >
          Image
        </button>

        {/* Alignment */}
        <button
          onClick={() => editor.chain().focus().setTextAlign('left').run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive({ textAlign: 'left' })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          ←
        </button>

        <button
          onClick={() => editor.chain().focus().setTextAlign('center').run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive({ textAlign: 'center' })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          ↔
        </button>

        <button
          onClick={() => editor.chain().focus().setTextAlign('right').run()}
          className={`px-3 py-1 text-sm font-medium rounded ${
            editor.isActive({ textAlign: 'right' })
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          →
        </button>
      </div>

      {/* Editor */}
      <EditorContent
        editor={editor}
        className={`min-h-[300px] focus:outline-none ${isRTL ? 'text-right' : 'text-left'}`}
        style={{ direction: currentLang.dir }}
      />
      <div className="p-4">
        <div 
          className={`prose max-w-none ${isRTL ? 'prose-rtl' : ''}`}
          dir={currentLang.dir}
        />
      </div>
    </div>
  );
};

export default RichTextEditor;